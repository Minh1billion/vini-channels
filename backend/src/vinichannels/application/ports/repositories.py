from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from vinichannels.domain.analytics.scoring import ScoreWeights
from vinichannels.domain.audit.entities import AuditAction, AuditEntry
from vinichannels.domain.channels.entities import Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.identity.entities import User
from vinichannels.domain.notifications.entities import Notification, PushSubscription
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import ChannelId, PartnerId, SyncRunId, UserId, VideoId
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus
from vinichannels.domain.syncing.providers import ProviderConfig, ProviderKey


class UserRepository(Protocol):
    async def add(self, user: User) -> None: ...

    async def save(self, user: User) -> None: ...

    async def get(self, user_id: UserId) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def list_all(self) -> list[User]: ...

    async def count(self) -> int: ...


class PartnerRepository(Protocol):
    async def add(self, partner: Partner) -> None: ...

    async def save(self, partner: Partner) -> None: ...

    async def get(self, partner_id: PartnerId) -> Partner | None: ...

    async def get_by_name(self, name: str) -> Partner | None: ...

    async def list_all(
        self,
        include_archived: bool = False,
        tag: str | None = None,
        search: str | None = None,
    ) -> list[Partner]: ...


class ChannelRepository(Protocol):
    async def add(self, channel: Channel) -> None: ...

    async def save(self, channel: Channel) -> None: ...

    async def get(self, channel_id: ChannelId) -> Channel | None: ...

    async def get_by_handle(self, handle: Handle) -> Channel | None: ...

    async def list_all(
        self,
        partner_id: PartnerId | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> list[Channel]: ...

    async def active_counts_by_partner(self) -> dict[PartnerId, int]: ...


class ChannelCredentialRepository(Protocol):
    async def get(self, channel_id: ChannelId) -> ChannelCredential | None: ...

    async def save(self, credential: ChannelCredential) -> None: ...


class ProviderConfigRepository(Protocol):
    async def get(self, key: ProviderKey) -> ProviderConfig | None: ...

    async def save(self, config: ProviderConfig) -> None: ...

    async def list_all(self) -> list[ProviderConfig]: ...


class SyncRunRepository(Protocol):
    async def add(self, run: SyncRun) -> None: ...

    async def save(self, run: SyncRun) -> None: ...

    async def get(self, run_id: SyncRunId) -> SyncRun | None: ...

    async def count_usage(self, source: str, since: datetime) -> int: ...

    async def list_recent(
        self,
        limit: int,
        status: SyncStatus | None = None,
        channel_id: ChannelId | None = None,
    ) -> list[SyncRun]: ...

    async def latest_slots(self) -> dict[ChannelId, datetime]: ...


class VideoRepository(Protocol):
    async def get_by_platform_ids(
        self, channel_id: ChannelId, platform_video_ids: Sequence[str]
    ) -> dict[str, Video]: ...

    async def save(self, video: Video) -> None: ...

    async def list_for_channel(
        self,
        channel_id: ChannelId,
        posted_from: datetime | None = None,
        posted_until: datetime | None = None,
    ) -> list[Video]: ...

    async def search(self, text: str, limit: int) -> list[Video]: ...


class SnapshotRepository(Protocol):
    async def add_channel_snapshot(self, snapshot: ChannelSnapshot) -> None: ...

    async def add_video_snapshots(self, snapshots: Sequence[VideoSnapshot]) -> None: ...

    async def latest_channel_snapshot(self, channel_id: ChannelId) -> ChannelSnapshot | None: ...

    async def channel_snapshots(
        self, channel_id: ChannelId, since: datetime, until: datetime
    ) -> list[ChannelSnapshot]: ...

    async def video_snapshots(
        self, video_ids: Sequence[VideoId], since: datetime, until: datetime
    ) -> list[VideoSnapshot]: ...

    async def earliest_activity(
        self, channel_ids: Sequence[ChannelId] | None = None
    ) -> datetime | None: ...


class ScoringSettingsRepository(Protocol):
    async def get(self) -> ScoreWeights | None: ...

    async def save(self, weights: ScoreWeights) -> None: ...


@dataclass(frozen=True, slots=True)
class AuditFilter:
    actor_id: str | None = None
    action: AuditAction | None = None
    since: datetime | None = None
    until: datetime | None = None


class AuditLogRepository(Protocol):
    async def add(self, entry: AuditEntry) -> None: ...

    async def search(self, criteria: AuditFilter, limit: int, offset: int) -> list[AuditEntry]: ...


class NotificationRepository(Protocol):
    async def add(self, notification: Notification) -> None: ...

    async def exists(self, dedupe_key: str) -> bool: ...

    async def get(self, notification_id: str) -> Notification | None: ...

    async def save(self, notification: Notification) -> None: ...

    async def list_recent(self, limit: int, unread_only: bool = False) -> list[Notification]: ...

    async def count_unread(self) -> int: ...

    async def mark_all_read(self, at: datetime) -> int: ...


class PushSubscriptionRepository(Protocol):
    async def upsert(self, subscription: PushSubscription) -> None: ...

    async def remove(self, user_id: UserId, endpoint: str) -> None: ...

    async def remove_endpoints(self, endpoints: Sequence[str]) -> None: ...

    async def list_all(self) -> list[PushSubscription]: ...
