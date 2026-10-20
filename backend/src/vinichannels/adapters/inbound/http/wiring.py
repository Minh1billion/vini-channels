from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from vinichannels.application.use_cases.analytics.compare import CompareChannels
from vinichannels.application.use_cases.analytics.growth import GetChannelDailyViews, GetVideoGrowth
from vinichannels.application.use_cases.analytics.metrics import GetChannelMetrics, ListVideos
from vinichannels.application.use_cases.analytics.overview import GetChannelTrend, GetOverview
from vinichannels.application.use_cases.audit.query import ListAuditLog
from vinichannels.application.use_cases.channels.crud import (
    ArchiveChannel,
    GetChannel,
    ListChannels,
    RestoreChannel,
    SetChannelSchedule,
    UpdateChannel,
)
from vinichannels.application.use_cases.channels.register import RegisterChannel
from vinichannels.application.use_cases.identity.auth import (
    Authenticate,
    ChangeOwnPassword,
    Login,
)
from vinichannels.application.use_cases.identity.users import CreateUser, ListUsers, UpdateUser
from vinichannels.application.use_cases.notifications.inbox import (
    ListNotifications,
    MarkAllNotificationsRead,
    MarkNotificationRead,
)
from vinichannels.application.use_cases.partners.crud import (
    ArchivePartner,
    CreatePartner,
    GetPartner,
    ListPartners,
    RestorePartner,
    UpdatePartner,
)
from vinichannels.application.use_cases.reports.export import ExportReport
from vinichannels.application.use_cases.scoring.scoring import (
    GetScoreboard,
    GetScoringWeights,
    UpdateScoringWeights,
)
from vinichannels.application.use_cases.search.global_search import GlobalSearch
from vinichannels.application.use_cases.syncing.history import ListSyncRuns, ListSyncSchedules
from vinichannels.application.use_cases.syncing.providers import (
    ListProviders,
    SetChannelCredential,
    UpdateProvider,
)
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel


@dataclass(frozen=True, slots=True)
class UseCases:
    login: Login
    authenticate: Authenticate
    change_own_password: ChangeOwnPassword
    global_search: GlobalSearch
    create_user: CreateUser
    list_users: ListUsers
    update_user: UpdateUser
    create_partner: CreatePartner
    update_partner: UpdatePartner
    archive_partner: ArchivePartner
    restore_partner: RestorePartner
    get_partner: GetPartner
    list_partners: ListPartners
    register_channel: RegisterChannel
    update_channel: UpdateChannel
    set_channel_schedule: SetChannelSchedule
    archive_channel: ArchiveChannel
    restore_channel: RestoreChannel
    get_channel: GetChannel
    list_channels: ListChannels
    sync_channel: SyncChannel
    list_sync_runs: ListSyncRuns
    list_sync_schedules: ListSyncSchedules
    list_providers: ListProviders
    update_provider: UpdateProvider
    set_channel_credential: SetChannelCredential
    get_channel_metrics: GetChannelMetrics
    compare_channels: CompareChannels
    get_daily_views: GetChannelDailyViews
    get_video_growth: GetVideoGrowth
    list_videos: ListVideos
    get_channel_trend: GetChannelTrend
    get_overview: GetOverview
    get_scoreboard: GetScoreboard
    export_report: ExportReport
    list_notifications: ListNotifications
    mark_notification_read: MarkNotificationRead
    mark_all_notifications_read: MarkAllNotificationsRead
    get_scoring_weights: GetScoringWeights
    update_scoring_weights: UpdateScoringWeights
    list_audit_log: ListAuditLog


@dataclass(frozen=True, slots=True)
class HttpConfig:
    cookie_name: str = "vini_session"
    cookie_secure: bool = False
    session_ttl_seconds: int = 12 * 3600
    cors_origins: tuple[str, ...] = ()


Hook = Callable[[], Awaitable[None]]
