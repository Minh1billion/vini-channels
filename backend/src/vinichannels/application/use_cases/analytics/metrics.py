from dataclasses import dataclass
from enum import StrEnum

from vinichannels.application.authorization import require
from vinichannels.application.dto import ChannelMetricsDTO, VideoDTO, VideoPageDTO
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.period import resolve_period
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.domain.analytics.metrics import (
    ChannelMetrics,
    VideoStats,
    change_ratio,
    compute_channel_metrics,
    engagement_rate_by_views,
)
from vinichannels.domain.analytics.periods import DateRange, PeriodSpec
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.ids import ChannelId

MAX_VIDEOS = 200


@dataclass(frozen=True, slots=True)
class PeriodData:
    channel_snapshots: list[ChannelSnapshot]
    videos: list[tuple[Video, VideoSnapshot]]


async def collect_period(uow: UnitOfWork, channel_id: ChannelId, period: DateRange) -> PeriodData:
    since, until = period.bounds()
    channel_snapshots = await uow.snapshots.channel_snapshots(channel_id, since, until)
    videos = await uow.videos.list_for_channel(channel_id, since, until)
    series = await uow.snapshots.video_snapshots([video.id for video in videos], since, until)
    latest = {snapshot.video_id: snapshot for snapshot in series}
    return PeriodData(channel_snapshots, [(v, latest[v.id]) for v in videos if v.id in latest])


def metrics_for(period: DateRange, data: PeriodData) -> ChannelMetrics:
    followers = [snapshot.followers for snapshot in data.channel_snapshots]
    return compute_channel_metrics(
        [VideoStats(s.views, s.likes, s.comments, s.shares, s.saves) for _, s in data.videos],
        followers[0] if followers else 0,
        followers[-1] if followers else 0,
        period,
    )


class GetChannelMetrics:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str, spec: PeriodSpec) -> ChannelMetricsDTO:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            period = await resolve_period(uow, self._clock, spec, [channel.id])
            before = period.previous()
            current = metrics_for(period, await collect_period(uow, channel.id, period))
            previous = metrics_for(before, await collect_period(uow, channel.id, before))
        return ChannelMetricsDTO(
            channel_id=channel.id,
            period_start=period.start,
            period_end=period.end,
            days=period.days,
            current=current,
            previous=previous,
            erv_change=change_ratio(current.erv, previous.erv),
            average_views_change=change_ratio(current.average_views, previous.average_views),
        )


class VideoSort(StrEnum):
    POSTED = "posted"
    VIEWS = "views"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    ERV = "erv"


def _sort_key(item: VideoDTO, sort: VideoSort) -> float | None:
    if sort is VideoSort.POSTED:
        return item.posted_at.timestamp()
    value: float | None = getattr(item, sort.value)
    return value


def _ordered(items: list[VideoDTO], sort: VideoSort, descending: bool) -> list[VideoDTO]:
    present = [item for item in items if _sort_key(item, sort) is not None]
    missing = [item for item in items if _sort_key(item, sort) is None]
    present.sort(key=lambda item: _sort_key(item, sort) or 0.0, reverse=descending)
    return present + missing


class ListVideos:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(
        self,
        actor: User,
        channel_id: str | None,
        spec: PeriodSpec,
        limit: int = 50,
        search: str | None = None,
        sort: VideoSort = VideoSort.POSTED,
        descending: bool = True,
    ) -> list[VideoDTO]:
        page = await self.page(actor, channel_id, spec, limit, 0, search, sort, descending)
        return page.items

    async def page(
        self,
        actor: User,
        channel_id: str | None,
        spec: PeriodSpec,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        sort: VideoSort = VideoSort.POSTED,
        descending: bool = True,
    ) -> VideoPageDTO:
        require(actor, Permission.ANALYTICS_READ)
        items: list[VideoDTO] = []
        async with self._uow_factory() as uow:
            period = await resolve_period(uow, self._clock, spec)
            if channel_id is None:
                channels = await uow.channels.list_all()
            else:
                channels = [await load_channel(uow, channel_id)]
            for channel in channels:
                data = await collect_period(uow, channel.id, period)
                items.extend(_video_dto(channel.handle.value, v, s) for v, s in data.videos)
        needle = search.strip().casefold() if search else ""
        if needle:
            items = [i for i in items if needle in i.caption.casefold() or needle in i.handle]
        capped = max(1, min(limit, MAX_VIDEOS))
        start = max(0, offset)
        ordered = _ordered(items, sort, descending)
        return VideoPageDTO(items=ordered[start : start + capped], total=len(ordered))


def _video_dto(handle: str, video: Video, snapshot: VideoSnapshot) -> VideoDTO:
    return VideoDTO(
        id=video.id,
        channel_id=video.channel_id,
        handle=handle,
        platform_video_id=video.platform_video_id,
        url=video.url,
        caption=video.caption,
        thumbnail_url=video.thumbnail_url,
        duration_sec=video.duration_sec,
        posted_at=video.posted_at,
        captured_at=snapshot.captured_at,
        views=snapshot.views,
        likes=snapshot.likes,
        comments=snapshot.comments,
        shares=snapshot.shares,
        saves=snapshot.saves,
        erv=engagement_rate_by_views(
            snapshot.likes, snapshot.comments, snapshot.shares, snapshot.views
        ),
    )
