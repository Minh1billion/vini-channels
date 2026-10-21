from copy import deepcopy
from types import TracebackType
from typing import Self

from vinichannels.adapters.outbound.memory.repositories import (
    MemoryAuditLogRepository,
    MemoryChannelCredentialRepository,
    MemoryChannelRepository,
    MemoryNotificationRepository,
    MemoryPartnerRepository,
    MemoryProviderConfigRepository,
    MemoryPushSubscriptionRepository,
    MemoryScoringSettingsRepository,
    MemorySnapshotRepository,
    MemoryState,
    MemorySyncRunRepository,
    MemoryUserRepository,
    MemoryVideoRepository,
)


class MemoryUnitOfWork:
    def __init__(self, committed: MemoryState) -> None:
        self._committed = committed
        self._working = MemoryState()
        self._bind()

    def _bind(self) -> None:
        self.users = MemoryUserRepository(self._working)
        self.partners = MemoryPartnerRepository(self._working)
        self.channels = MemoryChannelRepository(self._working)
        self.credentials = MemoryChannelCredentialRepository(self._working)
        self.providers = MemoryProviderConfigRepository(self._working)
        self.sync_runs = MemorySyncRunRepository(self._working)
        self.videos = MemoryVideoRepository(self._working)
        self.snapshots = MemorySnapshotRepository(self._working)
        self.scoring = MemoryScoringSettingsRepository(self._working)
        self.audit = MemoryAuditLogRepository(self._working)
        self.notifications = MemoryNotificationRepository(self._working)
        self.push_subscriptions = MemoryPushSubscriptionRepository(self._working)

    async def __aenter__(self) -> Self:
        self._working = deepcopy(self._committed)
        self._bind()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        snapshot = deepcopy(self._working)
        for name in MemoryState.__slots__:
            setattr(self._committed, name, getattr(snapshot, name))


class MemoryUnitOfWorkFactory:
    def __init__(self, state: MemoryState | None = None) -> None:
        self.state = state or MemoryState()

    def __call__(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)
