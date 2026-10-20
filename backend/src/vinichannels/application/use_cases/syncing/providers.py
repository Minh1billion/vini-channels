import json
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime

from vinichannels.application.authorization import require
from vinichannels.application.dto import UNSET, ChannelDTO, Maybe, ProviderDTO, Unset
from vinichannels.application.errors import NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.security import SecretCipher
from vinichannels.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import change, record
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.channels.entities import ChannelCredential
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.syncing.providers import (
    PROVIDER_SPECS,
    ProviderConfig,
    ProviderKey,
    month_start,
)


async def effective_config(uow: UnitOfWork, key: ProviderKey) -> ProviderConfig:
    return await uow.providers.get(key) or ProviderConfig.default_for(key)


def _resolve_key(key: str, available: Collection[ProviderKey]) -> ProviderKey:
    try:
        resolved = ProviderKey(key)
    except ValueError as error:
        raise NotFound("Không tìm thấy nguồn dữ liệu") from error
    if resolved not in available:
        raise NotFound("Không tìm thấy nguồn dữ liệu")
    return resolved


class ListProviders:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, clock: Clock, available: Collection[ProviderKey]
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._available = available

    async def execute(self, actor: User) -> list[ProviderDTO]:
        require(actor, Permission.SYNC_READ)
        since = month_start(self._clock.now())
        result: list[ProviderDTO] = []
        async with self._uow_factory() as uow:
            for key in sorted(self._available, key=lambda k: PROVIDER_SPECS[k].default_priority):
                config = await effective_config(uow, key)
                used = await uow.sync_runs.count_usage(key.value, since)
                result.append(ProviderDTO.from_entity(config, used))
        return sorted(result, key=lambda item: (item.priority, item.key))


@dataclass(frozen=True, slots=True)
class UpdateProviderCommand:
    key: str
    enabled: Maybe[bool] = UNSET
    priority: Maybe[int] = UNSET
    monthly_quota: Maybe[int | None] = UNSET
    credentials: Maybe[dict[str, str]] = UNSET


class UpdateProvider:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        cipher: SecretCipher,
        clock: Clock,
        available: Collection[ProviderKey],
    ) -> None:
        self._uow_factory = uow_factory
        self._cipher = cipher
        self._clock = clock
        self._available = available

    def _encode_credentials(self, key: ProviderKey, values: dict[str, str]) -> bytes | None:
        spec = PROVIDER_SPECS[key]
        cleaned = {name: value.strip() for name, value in values.items() if value.strip()}
        if not cleaned:
            return None
        unknown = set(cleaned) - set(spec.credential_fields)
        if unknown:
            raise ValidationError(f"Trường không hỗ trợ: {', '.join(sorted(unknown))}")
        required = set(spec.credential_fields) - set(spec.optional_fields)
        missing = required - set(cleaned)
        if missing:
            raise ValidationError(f"Thiếu thông tin: {', '.join(sorted(missing))}")
        return self._cipher.encrypt(json.dumps(cleaned))

    async def execute(self, actor: User, command: UpdateProviderCommand) -> ProviderDTO:
        require(actor, Permission.PROVIDERS_WRITE)
        key = _resolve_key(command.key, self._available)
        async with self._uow_factory() as uow:
            config = await effective_config(uow, key)
            changes: dict[str, str] = {}
            if not isinstance(command.enabled, Unset):
                if command.enabled != config.enabled:
                    changes["enabled"] = change(config.enabled, command.enabled)
                config.enabled = command.enabled
            if not isinstance(command.priority, Unset):
                if command.priority != config.priority:
                    changes["priority"] = change(config.priority, command.priority)
                config.priority = command.priority
            if not isinstance(command.monthly_quota, Unset):
                if command.monthly_quota is not None and command.monthly_quota < 0:
                    raise ValidationError("Hạn mức không được âm")
                if command.monthly_quota != config.monthly_quota:
                    changes["monthly_quota"] = change(config.monthly_quota, command.monthly_quota)
                config.monthly_quota = command.monthly_quota
            if not isinstance(command.credentials, Unset):
                config.credentials_enc = self._encode_credentials(key, command.credentials)
                changes["credentials"] = "updated" if config.credentials_enc else "cleared"
            if config.enabled and not config.is_configured:
                raise ValidationError("Cần nhập khóa trước khi bật nguồn này")
            await uow.providers.save(config)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.PROVIDER_UPDATE,
                "provider",
                key.value,
                PROVIDER_SPECS[key].label,
                changes,
            )
            used = await uow.sync_runs.count_usage(key.value, month_start(self._clock.now()))
            await uow.commit()
        return ProviderDTO.from_entity(config, used)


class SetChannelCredential:
    def __init__(self, uow_factory: UnitOfWorkFactory, cipher: SecretCipher, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._cipher = cipher
        self._clock = clock

    async def execute(
        self,
        actor: User,
        channel_id: str,
        access_token: str,
        expires_at: datetime,
        refresh_token: str | None = None,
    ) -> ChannelDTO:
        require(actor, Permission.PROVIDERS_WRITE)
        if not access_token.strip():
            raise ValidationError("Token truy cập không được để trống")
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            credential = ChannelCredential(
                channel_id=channel.id,
                access_token_enc=self._cipher.encrypt(access_token.strip()),
                refresh_token_enc=self._cipher.encrypt(refresh_token.strip())
                if refresh_token and refresh_token.strip()
                else b"",
                expires_at=expires_at,
            )
            channel.authorize(self._clock.now())
            await uow.credentials.save(credential)
            await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_TOKEN,
                "channel",
                channel.id,
                channel.handle.display,
                {"token": "updated"},
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)
