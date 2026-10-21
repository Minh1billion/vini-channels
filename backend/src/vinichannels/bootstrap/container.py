import asyncio
import signal
from datetime import timedelta

import httpx
from fastapi import FastAPI
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncEngine

from vinichannels.adapters.inbound.http.app import create_app
from vinichannels.adapters.inbound.http.wiring import HttpConfig, UseCases
from vinichannels.adapters.inbound.scheduler.loop import SchedulerLoop
from vinichannels.adapters.outbound.persistence.database import (
    create_engine,
    create_session_factory,
    migrate_to_head,
)
from vinichannels.adapters.outbound.persistence.unit_of_work import SqlUnitOfWork
from vinichannels.adapters.outbound.providers.apify import ApifyProvider
from vinichannels.adapters.outbound.providers.scrapecreators import ScrapeCreatorsProvider
from vinichannels.adapters.outbound.providers.tiktok import TikTokProvider, TikTokTokenRefresher
from vinichannels.adapters.outbound.push.webpush_sender import WebPushSender
from vinichannels.adapters.outbound.security.argon2_hasher import Argon2PasswordHasher
from vinichannels.adapters.outbound.security.fernet_cipher import FernetSecretCipher
from vinichannels.adapters.outbound.security.jwt_tokens import JwtSessionTokens
from vinichannels.adapters.outbound.storage.disabled import DisabledThumbnailStore
from vinichannels.adapters.outbound.storage.minio_store import MinioThumbnailStore
from vinichannels.adapters.outbound.system.system_clock import SystemClock
from vinichannels.application.ports.data_provider import DataProvider
from vinichannels.application.ports.thumbnails import ThumbnailStore
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.compare import CompareChannels
from vinichannels.application.use_cases.analytics.growth import (
    GetChannelDailyViews,
    GetPostingActivity,
    GetVideoGrowth,
)
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
    EnsureAdmin,
    Login,
)
from vinichannels.application.use_cases.identity.users import CreateUser, ListUsers, UpdateUser
from vinichannels.application.use_cases.jobs.fetch_jobs import (
    FetchJobs,
    ListFetchJobs,
    StartRegisterChannel,
    StartSyncChannel,
)
from vinichannels.application.use_cases.media.thumbnail import GetThumbnail
from vinichannels.application.use_cases.notifications.alerts import EvaluateAlerts
from vinichannels.application.use_cases.notifications.inbox import (
    ListNotifications,
    MarkAllNotificationsRead,
    MarkNotificationRead,
)
from vinichannels.application.use_cases.notifications.job_alerts import JobFinishedNotifier
from vinichannels.application.use_cases.notifications.push import (
    GetPushConfig,
    PushNotifier,
    SubscribePush,
    UnsubscribePush,
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
from vinichannels.application.use_cases.syncing.scheduled import RunDueSyncs
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel
from vinichannels.application.use_cases.syncing.token_refresh import RefreshChannelTokens
from vinichannels.bootstrap.settings import Settings
from vinichannels.domain.syncing.policies import RetryPolicy
from vinichannels.domain.syncing.providers import ProviderKey

RETRY_POLICY = RetryPolicy(max_attempts=3, base_delay_sec=2.0, max_delay_sec=10.0)


def _build_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=180.0))


def _build_providers(http_client: httpx.AsyncClient) -> dict[str, DataProvider]:
    return {
        ProviderKey.TIKTOK.value: TikTokProvider(http_client),
        ProviderKey.SCRAPECREATORS.value: ScrapeCreatorsProvider(http_client),
        ProviderKey.APIFY.value: ApifyProvider(http_client),
    }


def build_thumbnail_store(settings: Settings, http_client: httpx.AsyncClient) -> ThumbnailStore:
    if not settings.minio_endpoint:
        return DisabledThumbnailStore()
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    return MinioThumbnailStore(client, http_client, settings.minio_bucket)


def build_push_notifier(settings: Settings, uow_factory: UnitOfWorkFactory) -> PushNotifier | None:
    if not (settings.vapid_public_key and settings.vapid_private_key):
        return None
    sender = WebPushSender(settings.vapid_private_key, settings.vapid_subject)
    return PushNotifier(uow_factory, sender)


class SchedulerRuntime:
    def __init__(
        self,
        loop: SchedulerLoop,
        http_client: httpx.AsyncClient,
        engine: AsyncEngine,
    ) -> None:
        self._loop = loop
        self._http_client = http_client
        self._engine = engine

    async def run(self) -> None:
        stop = asyncio.Event()
        running = asyncio.get_running_loop()
        for name in (signal.SIGINT, signal.SIGTERM):
            running.add_signal_handler(name, stop.set)
        try:
            await self._loop.run_forever(stop)
        finally:
            await self._http_client.aclose()
            await self._engine.dispose()


def build_scheduler(settings: Settings) -> SchedulerRuntime:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    clock = SystemClock()
    http_client = _build_http_client()
    cipher = FernetSecretCipher(settings.secret_key)
    sync_channel = SyncChannel(
        uow_factory,
        _build_providers(http_client),
        cipher,
        clock,
        RETRY_POLICY,
        max_videos=settings.sync_max_videos or None,
        lookback_days=settings.sync_lookback_days or None,
        max_pages=settings.sync_max_pages,
        thumbnails=build_thumbnail_store(settings, http_client),
    )
    token_refresh = RefreshChannelTokens(
        uow_factory, TikTokTokenRefresher(http_client), cipher, clock
    )
    run_due = RunDueSyncs(
        uow_factory,
        sync_channel,
        clock,
        max_concurrency=settings.scheduler_concurrency,
        token_refresh=token_refresh,
        alerts=EvaluateAlerts(uow_factory, clock, build_push_notifier(settings, uow_factory)),
    )
    return SchedulerRuntime(
        SchedulerLoop(run_due, settings.scheduler_interval_sec), http_client, engine
    )


def build_app(
    settings: Settings,
    http_client: httpx.AsyncClient | None = None,
    thumbnail_store: ThumbnailStore | None = None,
) -> FastAPI:
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    clock = SystemClock()
    hasher = Argon2PasswordHasher()
    ttl = timedelta(hours=settings.session_ttl_hours)
    tokens = JwtSessionTokens(settings.secret_key, ttl)
    cipher = FernetSecretCipher(settings.secret_key)
    http_client = http_client or _build_http_client()
    providers = _build_providers(http_client)
    available = [ProviderKey(key) for key in providers]
    thumbnails = thumbnail_store or build_thumbnail_store(settings, http_client)

    job_alerts = JobFinishedNotifier(uow_factory, clock, build_push_notifier(settings, uow_factory))
    jobs = FetchJobs(clock, on_finish=job_alerts.notify)
    register_channel = RegisterChannel(
        uow_factory,
        providers,
        cipher,
        clock,
        RETRY_POLICY,
        max_pages=settings.backfill_max_pages,
        thumbnails=thumbnails,
    )
    sync_channel = SyncChannel(
        uow_factory,
        providers,
        cipher,
        clock,
        RETRY_POLICY,
        max_videos=settings.sync_max_videos or None,
        lookback_days=settings.sync_lookback_days or None,
        max_pages=settings.sync_max_pages,
        thumbnails=thumbnails,
    )
    get_channel_metrics = GetChannelMetrics(uow_factory, clock)
    get_scoreboard = GetScoreboard(uow_factory, clock)
    use_cases = UseCases(
        login=Login(uow_factory, hasher, tokens, clock),
        authenticate=Authenticate(uow_factory, tokens),
        change_own_password=ChangeOwnPassword(uow_factory, hasher, clock),
        global_search=GlobalSearch(uow_factory),
        create_user=CreateUser(uow_factory, hasher, clock),
        list_users=ListUsers(uow_factory),
        update_user=UpdateUser(uow_factory, hasher, clock),
        create_partner=CreatePartner(uow_factory, clock),
        update_partner=UpdatePartner(uow_factory, clock),
        archive_partner=ArchivePartner(uow_factory, clock),
        restore_partner=RestorePartner(uow_factory, clock),
        get_partner=GetPartner(uow_factory),
        list_partners=ListPartners(uow_factory),
        register_channel=register_channel,
        update_channel=UpdateChannel(uow_factory, clock),
        set_channel_schedule=SetChannelSchedule(uow_factory, clock),
        archive_channel=ArchiveChannel(uow_factory, clock),
        restore_channel=RestoreChannel(uow_factory, clock),
        get_channel=GetChannel(uow_factory),
        list_channels=ListChannels(uow_factory),
        sync_channel=sync_channel,
        list_sync_runs=ListSyncRuns(uow_factory),
        list_sync_schedules=ListSyncSchedules(uow_factory, clock),
        list_providers=ListProviders(uow_factory, clock, available),
        update_provider=UpdateProvider(uow_factory, cipher, clock, available),
        set_channel_credential=SetChannelCredential(uow_factory, cipher, clock),
        get_channel_metrics=get_channel_metrics,
        compare_channels=CompareChannels(get_channel_metrics),
        get_daily_views=GetChannelDailyViews(uow_factory, clock),
        get_video_growth=GetVideoGrowth(uow_factory, clock),
        get_posting_activity=GetPostingActivity(uow_factory, clock),
        list_videos=ListVideos(uow_factory, clock),
        get_channel_trend=GetChannelTrend(uow_factory, clock),
        get_overview=GetOverview(uow_factory, clock),
        get_scoreboard=get_scoreboard,
        export_report=ExportReport(uow_factory, clock, get_scoreboard),
        get_scoring_weights=GetScoringWeights(uow_factory),
        update_scoring_weights=UpdateScoringWeights(uow_factory, clock),
        list_audit_log=ListAuditLog(uow_factory),
        list_notifications=ListNotifications(uow_factory),
        mark_notification_read=MarkNotificationRead(uow_factory, clock),
        mark_all_notifications_read=MarkAllNotificationsRead(uow_factory, clock),
        get_push_config=GetPushConfig(
            settings.vapid_public_key
            if settings.vapid_public_key and settings.vapid_private_key
            else None
        ),
        subscribe_push=SubscribePush(uow_factory, clock),
        unsubscribe_push=UnsubscribePush(uow_factory),
        get_thumbnail=GetThumbnail(thumbnails),
        start_register_channel=StartRegisterChannel(jobs, register_channel),
        start_sync_channel=StartSyncChannel(jobs, sync_channel, uow_factory),
        list_fetch_jobs=ListFetchJobs(jobs),
    )
    config = HttpConfig(
        cookie_secure=settings.cookie_secure,
        session_ttl_seconds=int(ttl.total_seconds()),
        cors_origins=settings.cors_origins,
    )
    ensure_admin = EnsureAdmin(uow_factory, hasher)

    async def on_startup() -> None:
        await migrate_to_head(engine)
        if settings.admin_email and settings.admin_password:
            await ensure_admin.execute(settings.admin_email, settings.admin_password)

    async def on_shutdown() -> None:
        await jobs.shutdown()
        await http_client.aclose()
        await engine.dispose()

    return create_app(use_cases, config, on_startup, on_shutdown)
