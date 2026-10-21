from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from vinichannels.application.errors import DuplicateSyncRun
from vinichannels.application.ports.repositories import AuditFilter
from vinichannels.domain.analytics.scoring import ScoreWeights
from vinichannels.domain.audit.entities import AuditEntry
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


@dataclass(slots=True)
class MemoryState:
    users: dict[str, User] = field(default_factory=dict)
    partners: dict[str, Partner] = field(default_factory=dict)
    channels: dict[str, Channel] = field(default_factory=dict)
    credentials: dict[str, ChannelCredential] = field(default_factory=dict)
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    sync_runs: dict[str, SyncRun] = field(default_factory=dict)
    videos: dict[str, Video] = field(default_factory=dict)
    channel_snapshots: list[ChannelSnapshot] = field(default_factory=list)
    video_snapshots: list[VideoSnapshot] = field(default_factory=list)
    scoring_weights: ScoreWeights | None = None
    audit_entries: list[AuditEntry] = field(default_factory=list)
    notifications: dict[str, Notification] = field(default_factory=dict)
    push_subscriptions: dict[str, PushSubscription] = field(default_factory=dict)


def _matches(search: str | None, *values: str | None) -> bool:
    if not search:
        return True
    needle = search.strip().casefold()
    return any(needle in value.casefold() for value in values if value)


class MemoryUserRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.users

    async def add(self, user: User) -> None:
        self._items[user.id] = user

    async def save(self, user: User) -> None:
        self._items[user.id] = user

    async def get(self, user_id: UserId) -> User | None:
        return self._items.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        target = email.strip().lower()
        return next((user for user in self._items.values() if user.email == target), None)

    async def list_all(self) -> list[User]:
        return sorted(self._items.values(), key=lambda user: user.email)

    async def count(self) -> int:
        return len(self._items)


class MemoryPartnerRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.partners

    async def add(self, partner: Partner) -> None:
        self._items[partner.id] = partner

    async def save(self, partner: Partner) -> None:
        self._items[partner.id] = partner

    async def get(self, partner_id: PartnerId) -> Partner | None:
        return self._items.get(partner_id)

    async def get_by_name(self, name: str) -> Partner | None:
        target = name.strip().casefold()
        return next((p for p in self._items.values() if p.name.casefold() == target), None)

    async def list_all(
        self,
        include_archived: bool = False,
        tag: str | None = None,
        search: str | None = None,
    ) -> list[Partner]:
        wanted_tag = tag.strip().lower() if tag else None
        items = [
            partner
            for partner in self._items.values()
            if (include_archived or not partner.is_archived)
            and (wanted_tag is None or wanted_tag in partner.tags)
            and _matches(search, partner.name, partner.industry)
        ]
        return sorted(items, key=lambda partner: partner.name.casefold())


class MemoryChannelRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.channels

    async def add(self, channel: Channel) -> None:
        self._items[channel.id] = channel

    async def save(self, channel: Channel) -> None:
        self._items[channel.id] = channel

    async def get(self, channel_id: ChannelId) -> Channel | None:
        return self._items.get(channel_id)

    async def get_by_handle(self, handle: Handle) -> Channel | None:
        return next((c for c in self._items.values() if c.handle == handle), None)

    async def list_all(
        self,
        partner_id: PartnerId | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> list[Channel]:
        items = [
            channel
            for channel in self._items.values()
            if (partner_id is None or channel.partner_id == partner_id)
            and (include_archived or not channel.is_archived)
            and _matches(search, channel.handle.value, channel.display_name)
        ]
        return sorted(items, key=lambda channel: channel.handle.value)

    async def active_counts_by_partner(self) -> dict[PartnerId, int]:
        counts: dict[PartnerId, int] = {}
        for channel in self._items.values():
            if not channel.is_archived:
                counts[channel.partner_id] = counts.get(channel.partner_id, 0) + 1
        return counts


class MemoryChannelCredentialRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.credentials

    async def get(self, channel_id: ChannelId) -> ChannelCredential | None:
        return self._items.get(channel_id)

    async def save(self, credential: ChannelCredential) -> None:
        self._items[credential.channel_id] = credential


class MemoryProviderConfigRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.providers

    async def get(self, key: ProviderKey) -> ProviderConfig | None:
        return self._items.get(key.value)

    async def save(self, config: ProviderConfig) -> None:
        self._items[config.key.value] = config

    async def list_all(self) -> list[ProviderConfig]:
        return list(self._items.values())


class MemorySyncRunRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.sync_runs

    async def add(self, run: SyncRun) -> None:
        for other in self._items.values():
            if (other.channel_id, other.scheduled_for, other.trigger) == (
                run.channel_id,
                run.scheduled_for,
                run.trigger,
            ):
                raise DuplicateSyncRun("Lần đồng bộ này đã được tạo")
        self._items[run.id] = run

    async def save(self, run: SyncRun) -> None:
        self._items[run.id] = run

    async def get(self, run_id: SyncRunId) -> SyncRun | None:
        return self._items.get(run_id)

    async def count_usage(self, source: str, since: datetime) -> int:
        usable = {SyncStatus.SUCCESS, SyncStatus.PARTIAL}
        return sum(
            1
            for run in self._items.values()
            if run.source == source and run.status in usable and run.started_at >= since
        )

    async def latest_slots(self) -> dict[ChannelId, datetime]:
        slots: dict[ChannelId, datetime] = {}
        for run in self._items.values():
            current = slots.get(run.channel_id)
            if current is None or run.scheduled_for > current:
                slots[run.channel_id] = run.scheduled_for
        return slots

    async def list_recent(
        self,
        limit: int,
        status: SyncStatus | None = None,
        channel_id: ChannelId | None = None,
    ) -> list[SyncRun]:
        runs = [
            run
            for run in self._items.values()
            if (status is None or run.status is status)
            and (channel_id is None or run.channel_id == channel_id)
        ]
        return sorted(runs, key=lambda run: run.started_at, reverse=True)[:limit]


class MemoryVideoRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.videos

    async def get_by_platform_ids(
        self, channel_id: ChannelId, platform_video_ids: Sequence[str]
    ) -> dict[str, Video]:
        wanted = set(platform_video_ids)
        return {
            video.platform_video_id: video
            for video in self._items.values()
            if video.channel_id == channel_id and video.platform_video_id in wanted
        }

    async def save(self, video: Video) -> None:
        self._items[video.id] = video

    async def list_for_channel(
        self,
        channel_id: ChannelId,
        posted_from: datetime | None = None,
        posted_until: datetime | None = None,
    ) -> list[Video]:
        items = [
            video
            for video in self._items.values()
            if video.channel_id == channel_id
            and (posted_from is None or video.posted_at >= posted_from)
            and (posted_until is None or video.posted_at < posted_until)
        ]
        return sorted(items, key=lambda video: video.posted_at, reverse=True)

    async def search(self, text: str, limit: int) -> list[Video]:
        items = [video for video in self._items.values() if _matches(text, video.caption)]
        return sorted(items, key=lambda video: video.posted_at, reverse=True)[:limit]


class MemorySnapshotRepository:
    def __init__(self, state: MemoryState) -> None:
        self._state = state

    async def add_channel_snapshot(self, snapshot: ChannelSnapshot) -> None:
        self._state.channel_snapshots.append(snapshot)

    async def add_video_snapshots(self, snapshots: Sequence[VideoSnapshot]) -> None:
        self._state.video_snapshots.extend(snapshots)

    async def latest_channel_snapshot(self, channel_id: ChannelId) -> ChannelSnapshot | None:
        items = [item for item in self._state.channel_snapshots if item.channel_id == channel_id]
        return max(items, key=lambda item: item.captured_at, default=None)

    async def channel_snapshots(
        self, channel_id: ChannelId, since: datetime, until: datetime
    ) -> list[ChannelSnapshot]:
        items = [
            item
            for item in self._state.channel_snapshots
            if item.channel_id == channel_id and since <= item.captured_at < until
        ]
        return sorted(items, key=lambda item: item.captured_at)

    async def video_snapshots(
        self, video_ids: Sequence[VideoId], since: datetime, until: datetime
    ) -> list[VideoSnapshot]:
        wanted = set(video_ids)
        items = [
            item
            for item in self._state.video_snapshots
            if item.video_id in wanted and since <= item.captured_at < until
        ]
        return sorted(items, key=lambda item: item.captured_at)

    async def earliest_activity(
        self, channel_ids: Sequence[ChannelId] | None = None
    ) -> datetime | None:
        wanted = set(channel_ids) if channel_ids is not None else None
        stamps = [
            item.captured_at
            for item in self._state.channel_snapshots
            if wanted is None or item.channel_id in wanted
        ]
        stamps += [
            video.posted_at
            for video in self._state.videos.values()
            if wanted is None or video.channel_id in wanted
        ]
        return min(stamps, default=None)


class MemoryScoringSettingsRepository:
    def __init__(self, state: MemoryState) -> None:
        self._state = state

    async def get(self) -> ScoreWeights | None:
        return self._state.scoring_weights

    async def save(self, weights: ScoreWeights) -> None:
        self._state.scoring_weights = weights


class MemoryAuditLogRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.audit_entries

    async def add(self, entry: AuditEntry) -> None:
        self._items.append(entry)

    async def search(self, criteria: AuditFilter, limit: int, offset: int) -> list[AuditEntry]:
        found = [
            entry
            for entry in self._items
            if (criteria.actor_id is None or entry.actor_id == criteria.actor_id)
            and (criteria.action is None or entry.action is criteria.action)
            and (criteria.since is None or entry.occurred_at >= criteria.since)
            and (criteria.until is None or entry.occurred_at < criteria.until)
        ]
        found.sort(key=lambda entry: entry.occurred_at, reverse=True)
        return found[offset : offset + limit]


class MemoryNotificationRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.notifications

    async def add(self, notification: Notification) -> None:
        self._items[notification.id] = notification

    async def exists(self, dedupe_key: str) -> bool:
        return any(item.dedupe_key == dedupe_key for item in self._items.values())

    async def get(self, notification_id: str) -> Notification | None:
        return self._items.get(notification_id)

    async def save(self, notification: Notification) -> None:
        self._items[notification.id] = notification

    async def list_recent(self, limit: int, unread_only: bool = False) -> list[Notification]:
        items = [item for item in self._items.values() if not unread_only or not item.is_read]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    async def count_unread(self) -> int:
        return sum(1 for item in self._items.values() if not item.is_read)

    async def mark_all_read(self, at: datetime) -> int:
        unread = [item for item in self._items.values() if not item.is_read]
        for item in unread:
            item.mark_read(at)
        return len(unread)


class MemoryPushSubscriptionRepository:
    def __init__(self, state: MemoryState) -> None:
        self._items = state.push_subscriptions

    async def upsert(self, subscription: PushSubscription) -> None:
        existing = self._items.get(subscription.endpoint)
        if existing is None:
            self._items[subscription.endpoint] = subscription
        else:
            existing.user_id = subscription.user_id
            existing.p256dh = subscription.p256dh
            existing.auth = subscription.auth

    async def remove(self, user_id: UserId, endpoint: str) -> None:
        existing = self._items.get(endpoint)
        if existing is not None and existing.user_id == user_id:
            del self._items[endpoint]

    async def remove_endpoints(self, endpoints: Sequence[str]) -> None:
        for endpoint in endpoints:
            self._items.pop(endpoint, None)

    async def list_all(self) -> list[PushSubscription]:
        return sorted(self._items.values(), key=lambda item: item.created_at)
