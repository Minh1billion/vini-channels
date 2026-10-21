from collections import Counter
from datetime import timedelta, timezone

from vinichannels.application.authorization import require
from vinichannels.application.dto import (
    DailyPostsDTO,
    DailyViewsDTO,
    GrowthPointDTO,
    VideoGrowthDTO,
)
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.period import resolve_period
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.domain.analytics.metrics import views_at_age
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.analytics.views import daily_views, group_by_video, growth_curve
from vinichannels.domain.identity.entities import Permission, User

TOP_VIDEOS = 5
LOOKBACK = timedelta(days=1)


class GetChannelDailyViews:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str, spec: PeriodSpec) -> list[DailyViewsDTO]:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            period = await resolve_period(uow, self._clock, spec, [channel.id])
            since, until = period.bounds()
            videos = await uow.videos.list_for_channel(channel.id, None, until)
            snapshots = await uow.snapshots.video_snapshots(
                [video.id for video in videos], since - LOOKBACK, until
            )
        totals = daily_views(group_by_video(snapshots).values(), period)
        return [DailyViewsDTO(day, views) for day, views in sorted(totals.items())]


class GetPostingActivity:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str, spec: PeriodSpec) -> list[DailyPostsDTO]:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            period = await resolve_period(uow, self._clock, spec, [channel.id])
            since, until = period.bounds()
            videos = await uow.videos.list_for_channel(channel.id, since, until)
        zone = timezone(timedelta(minutes=period.offset_minutes))
        counts = Counter(video.posted_at.astimezone(zone).date() for video in videos)
        return [DailyPostsDTO(day, count) for day, count in sorted(counts.items())]


class GetVideoGrowth:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(
        self, actor: User, channel_id: str, spec: PeriodSpec, limit: int = TOP_VIDEOS
    ) -> list[VideoGrowthDTO]:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            period = await resolve_period(uow, self._clock, spec, [channel.id])
            since, until = period.bounds()
            videos = await uow.videos.list_for_channel(channel.id, since, until)
            snapshots = group_by_video(
                await uow.snapshots.video_snapshots([v.id for v in videos], since, until)
            )
        items: list[tuple[int, VideoGrowthDTO]] = []
        for video in videos:
            series = snapshots.get(video.id)
            if not series:
                continue
            latest = max(series, key=lambda item: item.captured_at).views
            curve = growth_curve(series, video.posted_at, period.days)
            items.append(
                (
                    latest,
                    VideoGrowthDTO(
                        video_id=video.id,
                        platform_video_id=video.platform_video_id,
                        caption=video.caption,
                        posted_at=video.posted_at,
                        views=latest,
                        views_24h=views_at_age(series, video.posted_at, timedelta(hours=24)),
                        views_72h=views_at_age(series, video.posted_at, timedelta(hours=72)),
                        curve=[GrowthPointDTO(age, views) for age, views in curve],
                    ),
                )
            )
        items.sort(key=lambda pair: pair[0], reverse=True)
        return [dto for _, dto in items[: max(1, min(limit, TOP_VIDEOS))]]
