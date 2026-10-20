import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from vinichannels.application.errors import NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.data_provider import ProviderError, ProviderUnavailable
from vinichannels.application.ports.security import SecretCipher
from vinichannels.application.ports.token_refresh import (
    RefreshedToken,
    RefreshRequest,
    TokenRefresher,
)
from vinichannels.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import record_system
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.channels.entities import Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode
from vinichannels.domain.syncing.policies import SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderKey

_log = logging.getLogger(__name__)

DEFAULT_REFRESH_WINDOW = timedelta(hours=6)
NO_REFRESH_TOKEN_REASON = "Không còn refresh token hợp lệ để gia hạn"


class _Outcome(StrEnum):
    REFRESHED = "refreshed"
    REVOKED = "revoked"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class TokenRefreshReport:
    due: int = 0
    refreshed: int = 0
    revoked: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass(frozen=True, slots=True)
class _Candidate:
    channel_id: str
    credential: ChannelCredential


class RefreshChannelTokens:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        refresher: TokenRefresher,
        cipher: SecretCipher,
        clock: Clock,
        window: timedelta = DEFAULT_REFRESH_WINDOW,
        max_batch: int = 100,
    ) -> None:
        self._uow_factory = uow_factory
        self._refresher = refresher
        self._cipher = cipher
        self._clock = clock
        self._window = window
        self._max_batch = max(1, max_batch)

    async def execute(self) -> TokenRefreshReport:
        now = self._clock.now()
        candidates: list[_Candidate] = []
        async with self._uow_factory() as uow:
            app = await self._app_credentials(uow)
            for channel in await uow.channels.list_all():
                if not self._eligible(channel):
                    continue
                credential = await uow.credentials.get(channel.id)
                if credential is not None and credential.expires_within(now, self._window):
                    candidates.append(_Candidate(channel.id, credential))
        batch = sorted(candidates, key=lambda item: item.credential.expires_at)[: self._max_batch]
        counts = dict.fromkeys(_Outcome, 0)
        for candidate in batch:
            try:
                counts[await self._refresh_one(candidate, app)] += 1
            except Exception:
                _log.exception(
                    "Làm mới token kênh %s gặp lỗi không lường trước", candidate.channel_id
                )
                counts[_Outcome.FAILED] += 1
        return TokenRefreshReport(
            due=len(candidates),
            refreshed=counts[_Outcome.REFRESHED],
            revoked=counts[_Outcome.REVOKED],
            failed=counts[_Outcome.FAILED],
            skipped=counts[_Outcome.SKIPPED],
        )

    @staticmethod
    def _eligible(channel: Channel) -> bool:
        return channel.is_syncable and channel.connection_mode is ConnectionMode.AUTHORIZED

    async def _app_credentials(self, uow: UnitOfWork) -> tuple[str, str] | None:
        config = await uow.providers.get(ProviderKey.TIKTOK)
        if config is None or config.credentials_enc is None:
            return None
        values = json.loads(self._cipher.decrypt(config.credentials_enc))
        key, secret = values.get("client_key"), values.get("client_secret")
        return (key, secret) if key and secret else None

    async def _refresh_one(self, candidate: _Candidate, app: tuple[str, str] | None) -> _Outcome:
        credential = candidate.credential
        now = self._clock.now()
        refresh_token = (
            self._cipher.decrypt(credential.refresh_token_enc)
            if credential.refresh_token_enc
            else ""
        )
        if not refresh_token or not credential.can_refresh(now):
            if credential.is_expired(now):
                return await self._revoke(candidate, NO_REFRESH_TOKEN_REASON)
            return _Outcome.SKIPPED
        if app is None:
            return _Outcome.SKIPPED
        try:
            token = await self._refresher.refresh(RefreshRequest(refresh_token, app[0], app[1]))
        except ProviderError as error:
            if error.kind is SyncErrorKind.TOKEN_REVOKED:
                return await self._revoke(candidate, error.message)
            _log.warning("Chưa làm mới được token kênh %s: %s", candidate.channel_id, error.message)
            return _Outcome.FAILED
        except ProviderUnavailable as error:
            _log.warning("Chưa làm mới được token kênh %s: %s", candidate.channel_id, error.message)
            return _Outcome.FAILED
        return await self._store(candidate, token)

    async def _store(self, candidate: _Candidate, token: RefreshedToken) -> _Outcome:
        at = self._clock.now()
        async with self._uow_factory() as uow:
            try:
                channel = await load_channel(uow, candidate.channel_id)
            except NotFound:
                return _Outcome.SKIPPED
            current = await uow.credentials.get(channel.id)
            if current is None or current.access_token_enc != candidate.credential.access_token_enc:
                return _Outcome.SKIPPED
            refresh_enc = (
                self._cipher.encrypt(token.refresh_token)
                if token.refresh_token
                else current.refresh_token_enc
            )
            refresh_expires_at = (
                at + token.refresh_lifetime
                if token.refresh_lifetime
                else current.refresh_expires_at
            )
            await uow.credentials.save(
                ChannelCredential(
                    channel_id=channel.id,
                    access_token_enc=self._cipher.encrypt(token.access_token),
                    refresh_token_enc=refresh_enc,
                    expires_at=at + token.lifetime,
                    refresh_expires_at=refresh_expires_at,
                    scopes=token.scopes or current.scopes,
                )
            )
            channel.change_status(ChannelStatus.HEALTHY, at)
            await uow.channels.save(channel)
            await uow.commit()
        return _Outcome.REFRESHED

    async def _revoke(self, candidate: _Candidate, reason: str) -> _Outcome:
        at = self._clock.now()
        async with self._uow_factory() as uow:
            try:
                channel = await load_channel(uow, candidate.channel_id)
            except NotFound:
                return _Outcome.SKIPPED
            current = await uow.credentials.get(channel.id)
            if current is None or current.access_token_enc != candidate.credential.access_token_enc:
                return _Outcome.SKIPPED
            if channel.revoke(at) is None:
                return _Outcome.SKIPPED
            await uow.channels.save(channel)
            await record_system(
                uow,
                self._clock,
                AuditAction.CHANNEL_TOKEN_REVOKED,
                "channel",
                channel.id,
                channel.handle.display,
                {"reason": reason},
            )
            await uow.commit()
        return _Outcome.REVOKED
