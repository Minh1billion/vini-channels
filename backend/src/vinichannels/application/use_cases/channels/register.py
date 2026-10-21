import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from vinichannels.application.authorization import require
from vinichannels.application.dto import ChannelDTO
from vinichannels.application.errors import ChannelUnverified, Conflict
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.data_provider import (
    DataProvider,
    FetchRequest,
    ProviderData,
    ProviderError,
    ProviderUnavailable,
)
from vinichannels.application.ports.security import SecretCipher
from vinichannels.application.ports.thumbnails import ThumbnailStore
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.progress import Progress
from vinichannels.application.use_cases.audit.recording import record
from vinichannels.application.use_cases.channels.common import (
    load_active_partner,
    validate_schedule,
)
from vinichannels.application.use_cases.syncing.ingest import Sleep, fetch_with_retry, store_data
from vinichannels.application.use_cases.syncing.providers import effective_config
from vinichannels.application.use_cases.syncing.thumbnails import mirror_thumbnails
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.channels.entities import DEFAULT_TIMEZONE, Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, PartnerId, SyncRunId, new_id
from vinichannels.domain.syncing.entities import SyncRun, SyncTrigger
from vinichannels.domain.syncing.policies import RetryPolicy
from vinichannels.domain.syncing.providers import PROVIDER_SPECS, ProviderKey, month_start


@dataclass(frozen=True, slots=True)
class ChannelToken:
    access_token: str
    expires_at: datetime
    refresh_token: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterChannelCommand:
    partner_id: str
    handle: str
    provider: str
    display_name: str = ""
    sync_cron: str | None = None
    timezone: str = DEFAULT_TIMEZONE
    token: ChannelToken | None = None
    history_since: date | None = None


class RegisterChannel:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        providers: Mapping[str, DataProvider],
        cipher: SecretCipher,
        clock: Clock,
        retry: RetryPolicy | None = None,
        sleep: Sleep | None = None,
        max_videos: int | None = None,
        max_pages: int = 100,
        thumbnails: ThumbnailStore | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._providers = providers
        self._cipher = cipher
        self._clock = clock
        self._retry = retry or RetryPolicy()
        self._sleep = sleep
        self._max_videos = max_videos
        self._max_pages = max_pages
        self._thumbnails = thumbnails

    async def execute(
        self, actor: User, command: RegisterChannelCommand, progress: Progress | None = None
    ) -> ChannelDTO:
        require(actor, Permission.PARTNERS_WRITE)
        require(actor, Permission.SYNC_WRITE)
        key, provider = self._resolve(command.provider)
        spec = PROVIDER_SPECS[key]
        if spec.requires_channel_token:
            require(actor, Permission.PROVIDERS_WRITE)
        validate_schedule(command.sync_cron, command.timezone)
        since = self._history_start(command)
        handle = Handle(command.handle)
        credentials = await self._prepare(command, key, handle)
        started = self._clock.now()
        data = await self._crawl(provider, handle, credentials, spec.label, since, progress)
        if progress is not None:
            await progress("Đang lưu dữ liệu", 0, None)
        finished = self._clock.now()
        async with self._uow_factory() as uow:
            if await uow.channels.get_by_handle(handle) is not None:
                raise Conflict(f"Kênh {handle.display} đã tồn tại")
            channel = Channel(
                id=ChannelId(new_id()),
                partner_id=PartnerId(command.partner_id),
                handle=handle,
                display_name=command.display_name,
                sync_cron=command.sync_cron,
                timezone=command.timezone,
            )
            if command.token is not None:
                channel.authorize(finished)
            await uow.channels.add(channel)
            if command.token is not None:
                await uow.credentials.save(self._credential(channel, command.token))
            await store_data(uow, channel, data, key.value, finished)
            run = SyncRun(
                id=SyncRunId(new_id()),
                channel_id=channel.id,
                scheduled_for=started,
                trigger=SyncTrigger.MANUAL,
                started_at=started,
            )
            if data.warning:
                run.partially_succeed(
                    finished, key.value, len(data.videos), "partial", data.warning
                )
            else:
                run.succeed(finished, key.value, len(data.videos))
            await uow.sync_runs.add(run)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_REGISTER,
                "channel",
                channel.id,
                handle.display,
                {
                    "provider": key.value,
                    "partner_id": command.partner_id,
                    "token": "provided" if command.token is not None else "none",
                },
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)

    def _resolve(self, provider: str) -> tuple[ProviderKey, DataProvider]:
        try:
            key = ProviderKey(provider)
        except ValueError as error:
            raise ValidationError("Nguồn dữ liệu không hợp lệ") from error
        found = self._providers.get(key.value)
        if found is None:
            raise ValidationError("Nguồn dữ liệu chưa được hỗ trợ")
        return key, found

    def _credential(self, channel: Channel, token: ChannelToken) -> ChannelCredential:
        refresh = (token.refresh_token or "").strip()
        return ChannelCredential(
            channel_id=channel.id,
            access_token_enc=self._cipher.encrypt(token.access_token.strip()),
            refresh_token_enc=self._cipher.encrypt(refresh) if refresh else b"",
            expires_at=token.expires_at,
        )

    async def _prepare(
        self, command: RegisterChannelCommand, key: ProviderKey, handle: Handle
    ) -> dict[str, str]:
        spec = PROVIDER_SPECS[key]
        now = self._clock.now()
        async with self._uow_factory() as uow:
            await load_active_partner(uow, command.partner_id)
            if await uow.channels.get_by_handle(handle) is not None:
                raise Conflict(f"Kênh {handle.display} đã tồn tại")
            config = await effective_config(uow, key)
            if not config.enabled:
                raise Conflict(f"Nguồn {spec.label} đang tắt")
            if not config.is_configured:
                raise Conflict(f"Nguồn {spec.label} chưa có khóa API")
            used = await uow.sync_runs.count_usage(key.value, month_start(now))
            if config.quota_exhausted(used):
                raise Conflict(f"Nguồn {spec.label} đã hết hạn mức tháng này")
            values: dict[str, str] = {}
            if config.credentials_enc is not None:
                values = json.loads(self._cipher.decrypt(config.credentials_enc))
        if spec.requires_channel_token:
            token = command.token
            if token is None or not token.access_token.strip():
                raise ValidationError(f"{spec.label} cần token truy cập của kênh")
            if token.expires_at <= now:
                raise ValidationError("Token đã hết hạn")
            values["access_token"] = token.access_token.strip()
        return values

    def _history_start(self, command: RegisterChannelCommand) -> datetime | None:
        if command.history_since is None:
            return None
        zone = ZoneInfo(command.timezone)
        if command.history_since > self._clock.now().astimezone(zone).date():
            raise ValidationError("Ngày bắt đầu lấy dữ liệu không được ở tương lai")
        return datetime.combine(command.history_since, time.min, zone)

    async def _crawl(
        self,
        provider: DataProvider,
        handle: Handle,
        credentials: dict[str, str],
        label: str,
        since: datetime | None,
        progress: Progress | None,
    ) -> ProviderData:
        request = FetchRequest(
            handle=handle.value,
            platform_channel_id=None,
            credentials=credentials,
            max_videos=self._max_videos,
            now=self._clock.now(),
            since=since,
            max_pages=self._max_pages,
            progress=progress,
        )
        try:
            if self._sleep is None:
                data = await fetch_with_retry(provider, request, self._retry)
            else:
                data = await fetch_with_retry(provider, request, self._retry, self._sleep)
        except ProviderError as error:
            raise ChannelUnverified(
                f"Không crawl được {handle.display} bằng {label}: {error.message}"
            ) from error
        except ProviderUnavailable as error:
            raise ChannelUnverified(f"Nguồn {label} chưa sẵn sàng: {error.message}") from error
        return await mirror_thumbnails(self._thumbnails, data, progress)
