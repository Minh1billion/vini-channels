from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from vinichannels.application.ports.repositories import (
    AuditLogRepository,
    ChannelCredentialRepository,
    ChannelRepository,
    NotificationRepository,
    PartnerRepository,
    ProviderConfigRepository,
    PushSubscriptionRepository,
    ScoringSettingsRepository,
    SnapshotRepository,
    SyncRunRepository,
    UserRepository,
    VideoRepository,
)


class UnitOfWork(Protocol):
    users: UserRepository
    partners: PartnerRepository
    channels: ChannelRepository
    credentials: ChannelCredentialRepository
    providers: ProviderConfigRepository
    sync_runs: SyncRunRepository
    videos: VideoRepository
    snapshots: SnapshotRepository
    scoring: ScoringSettingsRepository
    audit: AuditLogRepository
    notifications: NotificationRepository
    push_subscriptions: PushSubscriptionRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]
