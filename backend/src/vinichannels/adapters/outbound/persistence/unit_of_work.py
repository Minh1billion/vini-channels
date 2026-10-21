from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vinichannels.adapters.outbound.persistence.repositories import (
    SqlAuditLogRepository,
    SqlNotificationRepository,
    SqlChannelCredentialRepository,
    SqlChannelRepository,
    SqlPartnerRepository,
    SqlProviderConfigRepository,
    SqlPushSubscriptionRepository,
    SqlScoringSettingsRepository,
    SqlSnapshotRepository,
    SqlSyncRunRepository,
    SqlUserRepository,
    SqlVideoRepository,
)
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


class SqlUnitOfWork:
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

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        session = self._session_factory()
        self._session = session
        self.users = SqlUserRepository(session)
        self.partners = SqlPartnerRepository(session)
        self.channels = SqlChannelRepository(session)
        self.credentials = SqlChannelCredentialRepository(session)
        self.providers = SqlProviderConfigRepository(session)
        self.sync_runs = SqlSyncRunRepository(session)
        self.videos = SqlVideoRepository(session)
        self.snapshots = SqlSnapshotRepository(session)
        self.scoring = SqlScoringSettingsRepository(session)
        self.audit = SqlAuditLogRepository(session)
        self.notifications = SqlNotificationRepository(session)
        self.push_subscriptions = SqlPushSubscriptionRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is not None:
            await self._session.rollback()
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        if self._session is not None:
            await self._session.commit()
