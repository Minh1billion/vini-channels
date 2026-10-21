from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

from vinichannels.domain.analytics.metrics import ChannelMetrics
from vinichannels.domain.analytics.scoring import ScoreWeights
from vinichannels.domain.audit.entities import AuditAction, AuditEntry
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.notifications.entities import Notification
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus, SyncTrigger
from vinichannels.domain.syncing.providers import PROVIDER_SPECS, ProviderConfig


class Unset:
    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final = Unset()

type Maybe[T] = T | Unset


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: str
    email: str
    role: Role
    is_active: bool

    @classmethod
    def from_entity(cls, user: User) -> "UserDTO":
        return cls(id=user.id, email=user.email, role=user.role, is_active=user.is_active)


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: UserDTO
    token: str


@dataclass(frozen=True, slots=True)
class PartnerDTO:
    id: str
    name: str
    industry: str | None
    owner_user_id: str | None
    logo_url: str | None
    notes: str
    tags: tuple[str, ...]
    archived_at: datetime | None
    channel_count: int

    @classmethod
    def from_entity(cls, partner: Partner, channel_count: int = 0) -> "PartnerDTO":
        return cls(
            id=partner.id,
            name=partner.name,
            industry=partner.industry,
            owner_user_id=partner.owner_user_id,
            logo_url=partner.logo_url,
            notes=partner.notes,
            tags=tuple(sorted(partner.tags)),
            archived_at=partner.archived_at,
            channel_count=channel_count,
        )


@dataclass(frozen=True, slots=True)
class ChannelDTO:
    id: str
    partner_id: str
    handle: str
    display_name: str
    avatar_url: str | None
    connection_mode: ConnectionMode
    status: ChannelStatus
    sync_cron: str | None
    timezone: str
    is_active: bool
    archived_at: datetime | None

    @classmethod
    def from_entity(cls, channel: Channel) -> "ChannelDTO":
        return cls(
            id=channel.id,
            partner_id=channel.partner_id,
            handle=channel.handle.value,
            display_name=channel.display_name,
            avatar_url=channel.avatar_url,
            connection_mode=channel.connection_mode,
            status=channel.status,
            sync_cron=channel.sync_cron,
            timezone=channel.timezone,
            is_active=channel.is_active,
            archived_at=channel.archived_at,
        )


@dataclass(frozen=True, slots=True)
class SyncRunDTO:
    id: str
    channel_id: str
    handle: str
    trigger: SyncTrigger
    status: SyncStatus
    source: str | None
    items_fetched: int
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
    error_code: str | None
    error_message: str | None

    @classmethod
    def from_entity(cls, run: SyncRun, handle: str) -> "SyncRunDTO":
        return cls(
            id=run.id,
            channel_id=run.channel_id,
            handle=handle,
            trigger=run.trigger,
            status=run.status,
            source=run.source,
            items_fetched=run.items_fetched,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_sec=run.duration_sec,
            error_code=run.error_code,
            error_message=run.error_message,
        )


@dataclass(frozen=True, slots=True)
class ProviderDTO:
    key: str
    label: str
    enabled: bool
    priority: int
    monthly_quota: int | None
    used_this_month: int
    is_configured: bool
    credential_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    requires_channel_token: bool

    @classmethod
    def from_entity(cls, config: ProviderConfig, used_this_month: int) -> "ProviderDTO":
        spec = PROVIDER_SPECS[config.key]
        return cls(
            key=config.key.value,
            label=spec.label,
            enabled=config.enabled,
            priority=config.priority,
            monthly_quota=config.monthly_quota,
            used_this_month=used_this_month,
            is_configured=config.is_configured,
            credential_fields=spec.credential_fields,
            optional_fields=spec.optional_fields,
            requires_channel_token=spec.requires_channel_token,
        )


@dataclass(frozen=True, slots=True)
class SyncScheduleDTO:
    channel_id: str
    handle: str
    display_name: str
    connection_mode: ConnectionMode
    status: ChannelStatus
    is_active: bool
    cron: str
    is_default_cron: bool
    timezone: str
    next_run_at: datetime | None


@dataclass(frozen=True, slots=True)
class ChannelMetricsDTO:
    channel_id: str
    period_start: date
    period_end: date
    days: int
    current: ChannelMetrics
    previous: ChannelMetrics
    erv_change: float | None
    average_views_change: float | None


@dataclass(frozen=True, slots=True)
class VideoDTO:
    id: str
    channel_id: str
    handle: str
    platform_video_id: str
    url: str | None
    caption: str
    thumbnail_url: str | None
    duration_sec: int
    posted_at: datetime
    captured_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: int | None
    erv: float | None


@dataclass(frozen=True, slots=True)
class VideoPageDTO:
    items: list[VideoDTO]
    total: int


@dataclass(frozen=True, slots=True)
class ChannelScoreDTO:
    channel_id: str
    partner_id: str
    partner_name: str
    handle: str
    display_name: str
    rank: int | None
    total: float | None
    components: dict[str, float | None]
    erv: float | None
    follower_growth_ratio: float | None
    reach_ratio: float | None
    posts_per_week: float | None


@dataclass(frozen=True, slots=True)
class PartnerScoreDTO:
    partner_id: str
    name: str
    rank: int | None
    total: float | None
    channel_count: int
    scored_channel_count: int


@dataclass(frozen=True, slots=True)
class ScoreboardDTO:
    period_start: date
    period_end: date
    days: int
    weights: ScoreWeights
    channels: list[ChannelScoreDTO]
    partners: list[PartnerScoreDTO]


@dataclass(frozen=True, slots=True)
class TrendPointDTO:
    day: date
    followers: int
    total_likes: int
    video_count: int


@dataclass(frozen=True, slots=True)
class ChannelOverviewDTO:
    channel_id: str
    followers: int | None
    follower_growth: int
    follower_growth_ratio: float | None
    views: int
    video_count: int
    average_views: float | None
    erv: float | None


@dataclass(frozen=True, slots=True)
class OverviewDTO:
    period_start: date
    period_end: date
    days: int
    channel_count: int
    followers: int
    follower_growth: int
    views: int
    views_change: float | None
    video_count: int
    video_count_change: float | None
    erv: float | None
    erv_change: float | None
    channels: list[ChannelOverviewDTO]


@dataclass(frozen=True, slots=True)
class AuditEntryDTO:
    id: str
    actor_id: str
    actor_email: str
    action: AuditAction
    target_type: str
    target_id: str
    target_label: str
    detail: dict[str, str]
    occurred_at: datetime

    @classmethod
    def from_entity(cls, entry: AuditEntry) -> "AuditEntryDTO":
        return cls(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_email=entry.actor_email,
            action=entry.action,
            target_type=entry.target_type,
            target_id=entry.target_id,
            target_label=entry.target_label,
            detail=dict(entry.detail),
            occurred_at=entry.occurred_at,
        )


@dataclass(frozen=True, slots=True)
class DailyViewsDTO:
    day: date
    views: int


@dataclass(frozen=True, slots=True)
class DailyPostsDTO:
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class GrowthPointDTO:
    age_days: int
    views: int


@dataclass(frozen=True, slots=True)
class VideoGrowthDTO:
    video_id: str
    platform_video_id: str
    caption: str
    posted_at: datetime
    views: int
    views_24h: int | None
    views_72h: int | None
    curve: list[GrowthPointDTO]


@dataclass(frozen=True, slots=True)
class NotificationListDTO:
    items: list[Notification]
    unread_count: int


@dataclass(frozen=True, slots=True)
class SearchVideoHit:
    id: str
    channel_id: str
    handle: str
    caption: str
    thumbnail_url: str | None
    posted_at: datetime


@dataclass(frozen=True, slots=True)
class SearchResultDTO:
    partners: list[PartnerDTO]
    channels: list[ChannelDTO]
    videos: list[SearchVideoHit]
