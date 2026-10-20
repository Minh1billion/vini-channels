from vinichannels.application.authorization import require
from vinichannels.application.dto import ChannelOverviewDTO, OverviewDTO, TrendPointDTO
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.metrics import collect_period, metrics_for
from vinichannels.application.use_cases.analytics.period import resolve_period
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.domain.analytics.metrics import (
    ChannelMetrics,
    change_ratio,
    pooled_engagement_rate,
)
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.identity.entities import Permission, User


def _engagement(metrics: ChannelMetrics) -> tuple[int, int]:
    return (
        metrics.total_likes + metrics.total_comments + metrics.total_shares,
        metrics.total_views,
    )


class GetChannelTrend:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str, spec: PeriodSpec) -> list[TrendPointDTO]:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            period = await resolve_period(uow, self._clock, spec, [channel.id])
            since, until = period.bounds()
            snapshots = await uow.snapshots.channel_snapshots(channel.id, since, until)
        last_of_day = {snapshot.captured_at.date(): snapshot for snapshot in snapshots}
        return [
            TrendPointDTO(day, item.followers, item.total_likes, item.video_count)
            for day, item in sorted(last_of_day.items())
        ]


class GetOverview:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, spec: PeriodSpec) -> OverviewDTO:
        require(actor, Permission.ANALYTICS_READ)
        rows: list[ChannelOverviewDTO] = []
        current: list[ChannelMetrics] = []
        previous: list[ChannelMetrics] = []
        async with self._uow_factory() as uow:
            period = await resolve_period(uow, self._clock, spec)
            before = period.previous()
            partners = {partner.id for partner in await uow.partners.list_all()}
            channels = [c for c in await uow.channels.list_all() if c.partner_id in partners]
            for channel in channels:
                now_metrics = metrics_for(period, await collect_period(uow, channel.id, period))
                before_metrics = metrics_for(before, await collect_period(uow, channel.id, before))
                latest = await uow.snapshots.latest_channel_snapshot(channel.id)
                current.append(now_metrics)
                previous.append(before_metrics)
                rows.append(
                    ChannelOverviewDTO(
                        channel_id=channel.id,
                        followers=latest.followers if latest else None,
                        follower_growth=now_metrics.follower_growth,
                        follower_growth_ratio=now_metrics.follower_growth_ratio,
                        views=now_metrics.total_views,
                        video_count=now_metrics.video_count,
                        average_views=now_metrics.average_views,
                        erv=now_metrics.erv,
                    )
                )
        views = sum(m.total_views for m in current)
        videos = sum(m.video_count for m in current)
        erv = pooled_engagement_rate(_engagement(m) for m in current)
        return OverviewDTO(
            period_start=period.start,
            period_end=period.end,
            days=period.days,
            channel_count=len(rows),
            followers=sum(row.followers or 0 for row in rows),
            follower_growth=sum(m.follower_growth for m in current),
            views=views,
            views_change=change_ratio(views, sum(m.total_views for m in previous)),
            video_count=videos,
            video_count_change=change_ratio(videos, sum(m.video_count for m in previous)),
            erv=erv,
            erv_change=change_ratio(erv, pooled_engagement_rate(_engagement(m) for m in previous)),
            channels=rows,
        )
