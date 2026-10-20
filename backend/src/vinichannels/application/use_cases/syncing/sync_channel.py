import asyncio
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from vinichannels.application.authorization import require
from vinichannels.application.dto import SyncRunDTO
from vinichannels.application.errors import Conflict
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.data_provider import (
    DataProvider,
    FetchRequest,
    ProviderData,
    ProviderError,
    ProviderUnavailable,
)
from vinichannels.application.ports.security import SecretCipher
from vinichannels.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.application.use_cases.syncing.ingest import Sleep, fetch_with_retry, store_data
from vinichannels.application.use_cases.syncing.providers import effective_config
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import InvalidStateError
from vinichannels.domain.shared.ids import SyncRunId, new_id
from vinichannels.domain.syncing.entities import SyncRun, SyncTrigger
from vinichannels.domain.syncing.policies import RetryPolicy, SyncErrorKind
from vinichannels.domain.syncing.providers import PROVIDER_SPECS, ProviderKey, month_start


@dataclass(frozen=True, slots=True)
class _Attempt:
    provider: DataProvider
    credentials: dict[str, str]


@dataclass(frozen=True, slots=True)
class _Job:
    run_id: SyncRunId
    handle: str
    platform_channel_id: str | None
    attempts: tuple[_Attempt, ...]


@dataclass(frozen=True, slots=True)
class _Outcome:
    source: str
    data: ProviderData | None = None
    kind: SyncErrorKind | None = None
    code: str = ""
    message: str = ""


class SyncChannel:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        providers: Mapping[str, DataProvider],
        cipher: SecretCipher,
        clock: Clock,
        retry: RetryPolicy | None = None,
        sleep: Sleep = asyncio.sleep,
        max_videos: int = 30,
    ) -> None:
        self._uow_factory = uow_factory
        self._providers = providers
        self._cipher = cipher
        self._clock = clock
        self._retry = retry or RetryPolicy()
        self._sleep = sleep
        self._max_videos = max_videos

    async def execute(
        self, actor: User, channel_id: str, trigger: SyncTrigger = SyncTrigger.MANUAL
    ) -> SyncRunDTO:
        require(actor, Permission.SYNC_WRITE)
        return await self.run(channel_id, trigger)

    async def run(
        self,
        channel_id: str,
        trigger: SyncTrigger,
        scheduled_for: datetime | None = None,
    ) -> SyncRunDTO:
        job = await self._start(channel_id, trigger, scheduled_for)
        outcome = await self._collect(job)
        return await self._finish(channel_id, job.run_id, outcome)

    async def _plan(self, uow: UnitOfWork, channel: Channel) -> tuple[_Attempt, ...]:
        now = self._clock.now()
        since = month_start(now)
        credential = await uow.credentials.get(channel.id)
        ranked = []
        for key_text, provider in self._providers.items():
            key = ProviderKey(key_text)
            config = await effective_config(uow, key)
            if not config.enabled or not config.is_configured:
                continue
            if config.quota_exhausted(await uow.sync_runs.count_usage(key_text, since)):
                continue
            spec = PROVIDER_SPECS[key]
            values: dict[str, str] = {}
            if config.credentials_enc is not None:
                values = json.loads(self._cipher.decrypt(config.credentials_enc))
            if spec.requires_channel_token:
                if (
                    channel.connection_mode is not ConnectionMode.AUTHORIZED
                    or credential is None
                    or credential.is_expired(now)
                ):
                    continue
                values["access_token"] = self._cipher.decrypt(credential.access_token_enc)
            ranked.append((config.priority, key_text, _Attempt(provider, values)))
        ranked.sort(key=lambda item: (item[0], item[1]))
        return tuple(item[2] for item in ranked)

    async def _start(
        self, channel_id: str, trigger: SyncTrigger, scheduled_for: datetime | None
    ) -> _Job:
        now = self._clock.now()
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            if not channel.is_syncable:
                raise InvalidStateError("Kênh này hiện không thể đồng bộ")
            attempts = await self._plan(uow, channel)
            if not attempts:
                raise Conflict("Chưa có nguồn dữ liệu nào sẵn sàng cho kênh này")
            run = SyncRun(
                id=SyncRunId(new_id()),
                channel_id=channel.id,
                scheduled_for=scheduled_for or now,
                trigger=trigger,
                started_at=now,
            )
            await uow.sync_runs.add(run)
            await uow.commit()
        return _Job(run.id, channel.handle.value, channel.platform_channel_id, attempts)

    async def _collect(self, job: _Job) -> _Outcome:
        outcome = _Outcome(source="", code="no_attempt")
        for attempt in job.attempts:
            key = attempt.provider.key
            request = FetchRequest(
                handle=job.handle,
                platform_channel_id=job.platform_channel_id,
                credentials=attempt.credentials,
                max_videos=self._max_videos,
                now=self._clock.now(),
            )
            try:
                data = await fetch_with_retry(attempt.provider, request, self._retry, self._sleep)
                return _Outcome(source=key, data=data)
            except ProviderError as error:
                outcome = _Outcome(
                    source=key, kind=error.kind, code=error.kind.value, message=error.message
                )
                if not error.kind.is_transient:
                    return outcome
            except ProviderUnavailable as error:
                outcome = _Outcome(source=key, code="provider_unavailable", message=error.message)
        return outcome

    async def _finish(self, channel_id: str, run_id: SyncRunId, outcome: _Outcome) -> SyncRunDTO:
        at = self._clock.now()
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            run = await uow.sync_runs.get(run_id)
            if run is None:
                raise Conflict("Không tìm thấy lần đồng bộ")
            if outcome.data is not None:
                await store_data(uow, channel, outcome.data, outcome.source, at)
                items = len(outcome.data.videos)
                if outcome.data.warning:
                    run.partially_succeed(
                        at, outcome.source, items, "partial", outcome.data.warning
                    )
                else:
                    run.succeed(at, outcome.source, items)
            else:
                if outcome.kind is not None:
                    channel.change_status(
                        outcome.kind.resulting_channel_status or ChannelStatus.PROVIDER_ERROR, at
                    )
                    await uow.channels.save(channel)
                run.fail(at, outcome.code, outcome.message, outcome.source)
            await uow.sync_runs.save(run)
            await uow.commit()
        return SyncRunDTO.from_entity(run, channel.handle.value)
