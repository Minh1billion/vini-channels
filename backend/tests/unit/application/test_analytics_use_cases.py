from datetime import UTC, datetime

import pytest

from tests.unit.application.conftest import World, add_channel, run
from vinichannels.application.errors import NotFound
from vinichannels.application.use_cases.analytics.compare import CompareChannels
from vinichannels.application.use_cases.analytics.growth import GetChannelDailyViews, GetVideoGrowth
from vinichannels.application.use_cases.analytics.metrics import (
    GetChannelMetrics,
    ListVideos,
    VideoSort,
)
from vinichannels.application.use_cases.analytics.overview import GetChannelTrend, GetOverview
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.identity.entities import User
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, VideoId

LAST_7 = PeriodSpec.last(7)


def at(day: int, hour: int = 8) -> datetime:
    return datetime(2026, 10, day, hour, tzinfo=UTC)


def seed_video(
    world: World, channel_id: str, key: str, posted: datetime, *stats: tuple[datetime, int, int]
) -> None:
    video = Video(VideoId(key), ChannelId(channel_id), key, posted)
    world.uow.state.videos[video.id] = video
    for captured, views, likes in stats:
        world.uow.state.video_snapshots.append(
            VideoSnapshot(video.id, captured, "apify", views, likes, 0, 0)
        )


def seed_followers(world: World, channel_id: str, *points: tuple[datetime, int]) -> None:
    for captured, followers in points:
        world.uow.state.channel_snapshots.append(
            ChannelSnapshot(ChannelId(channel_id), captured, "apify", followers)
        )


@pytest.fixture
def channel_id(world: World, manager: User) -> str:
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha"))
    return add_channel(world, partner.id, "alpha").id


def test_follower_growth_and_engagement_over_period(
    world: World, manager: User, channel_id: str
) -> None:
    seed_followers(world, channel_id, (at(13), 1000), (at(16), 1050), (at(19, 6), 1100))
    seed_followers(world, channel_id, (at(7), 900), (at(12), 1000))
    seed_video(world, channel_id, "a", at(14), (at(15), 100, 5), (at(18), 1000, 100))
    seed_video(world, channel_id, "b", at(15), (at(18), 1000, 50))
    seed_video(world, channel_id, "old", at(8), (at(10), 1000, 20))

    result = run(GetChannelMetrics(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert (result.period_start.day, result.period_end.day) == (13, 19)
    assert result.current.follower_growth == 100
    assert result.current.follower_growth_ratio == pytest.approx(0.1)
    assert result.current.video_count == 2
    assert result.current.total_views == 2000
    assert result.current.erv == pytest.approx(0.075)
    assert result.previous.video_count == 1
    assert result.previous.erv == pytest.approx(0.02)
    assert result.erv_change == pytest.approx(2.75)


def test_metrics_without_snapshots_are_empty(world: World, manager: User, channel_id: str) -> None:
    result = run(GetChannelMetrics(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert result.current.video_count == 0
    assert result.current.follower_growth == 0
    assert result.current.erv is None
    assert result.erv_change is None


def test_list_videos_uses_latest_snapshot_in_range(
    world: World, manager: User, channel_id: str
) -> None:
    seed_video(world, channel_id, "a", at(14), (at(15), 100, 5), (at(18), 1000, 100))
    seed_video(world, channel_id, "b", at(16), (at(18), 500, 25))
    seed_video(world, channel_id, "no-data", at(17))

    items = run(ListVideos(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert [item.platform_video_id for item in items] == ["b", "a"]
    assert items[1].views == 1000
    assert items[1].erv == pytest.approx(0.1)
    assert items[0].erv == pytest.approx(0.05)


def test_unknown_channel_is_not_found(world: World, manager: User) -> None:
    with pytest.raises(NotFound):
        run(GetChannelMetrics(world.uow, world.clock).execute(manager, "missing", LAST_7))


def test_trend_keeps_last_snapshot_of_each_day(
    world: World, manager: User, channel_id: str
) -> None:
    seed_followers(
        world, channel_id, (at(14, 6), 1000), (at(14, 20), 1040), (at(16), 1100), (at(1), 5)
    )

    points = run(GetChannelTrend(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert [(p.day.day, p.followers) for p in points] == [(14, 1040), (16, 1100)]


def test_overview_aggregates_channels_and_compares_with_previous_period(
    world: World, manager: User, channel_id: str
) -> None:
    other = add_channel(world, world.uow.state.channels[channel_id].partner_id, "beta").id
    seed_followers(world, channel_id, (at(13), 1000), (at(19), 1100))
    seed_followers(world, other, (at(14), 200), (at(18), 300))
    seed_video(world, channel_id, "a", at(14), (at(18), 1000, 100))
    seed_video(world, other, "b", at(15), (at(18), 1000, 50))
    seed_video(world, other, "c", at(8), (at(10), 1000, 25))

    result = run(GetOverview(world.uow, world.clock).execute(manager, LAST_7))

    assert result.channel_count == 2
    assert result.followers == 1400
    assert result.follower_growth == 200
    assert result.views == 2000
    assert result.erv == pytest.approx(0.075)
    assert result.views_change == pytest.approx(1.0)
    assert result.erv_change == pytest.approx(2.0)
    by_channel = {row.channel_id: row for row in result.channels}
    assert by_channel[other].follower_growth == 100
    assert by_channel[channel_id].erv == pytest.approx(0.1)


def test_list_videos_filters_and_sorts_across_channels(
    world: World, manager: User, channel_id: str
) -> None:
    other = add_channel(world, world.uow.state.channels[channel_id].partner_id, "beta").id
    seed_video(world, channel_id, "a", at(14), (at(18), 1000, 100))
    seed_video(world, other, "b", at(15), (at(18), 5000, 50))
    seed_video(world, other, "c", at(16), (at(18), 300, 30))
    use_case = ListVideos(world.uow, world.clock)

    by_views = run(use_case.execute(manager, None, LAST_7, sort=VideoSort.VIEWS))
    by_erv_asc = run(use_case.execute(manager, None, LAST_7, sort=VideoSort.ERV, descending=False))
    only_beta = run(use_case.execute(manager, None, LAST_7, search="beta", limit=1))

    assert [item.platform_video_id for item in by_views] == ["b", "a", "c"]
    assert [item.platform_video_id for item in by_erv_asc] == ["b", "a", "c"]
    assert [item.handle for item in by_views] == ["beta", "alpha", "beta"]
    assert len(only_beta) == 1
    assert only_beta[0].handle == "beta"


def _second_channel(world: World, manager: User) -> str:
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Beta"))
    return add_channel(world, partner.id, "beta").id


def test_compare_returns_metrics_per_channel(world: World, manager: User, channel_id: str) -> None:
    other = _second_channel(world, manager)
    seed_followers(world, channel_id, (at(13), 1000), (at(19, 6), 1100))
    seed_followers(world, other, (at(13), 200), (at(19, 6), 180))
    seed_video(world, channel_id, "a", at(14), (at(18), 1000, 100))
    seed_video(world, other, "b", at(15), (at(18), 400, 20), (at(19), 500, 25))

    result = run(
        CompareChannels(GetChannelMetrics(world.uow, world.clock)).execute(
            manager, [channel_id, other], LAST_7
        )
    )

    assert [item.channel_id for item in result] == [channel_id, other]
    assert result[0].current.total_views == 1000
    assert result[0].current.follower_growth == 100
    assert result[0].current.erv == pytest.approx(0.1)
    assert result[1].current.total_views == 500
    assert result[1].current.follower_growth == -20
    assert result[1].current.erv == pytest.approx(0.05)


def test_compare_rejects_too_many_or_too_few_channels(
    world: World, manager: User, channel_id: str
) -> None:
    use_case = CompareChannels(GetChannelMetrics(world.uow, world.clock))

    with pytest.raises(ValidationError):
        run(use_case.execute(manager, [str(n) for n in range(6)], LAST_7))
    with pytest.raises(ValidationError):
        run(use_case.execute(manager, [channel_id, channel_id], LAST_7))


def test_compare_unknown_channel_is_not_found(world: World, manager: User, channel_id: str) -> None:
    use_case = CompareChannels(GetChannelMetrics(world.uow, world.clock))

    with pytest.raises(NotFound):
        run(use_case.execute(manager, [channel_id, "missing"], LAST_7))


def test_daily_views_use_case_handles_missing_snapshot(
    world: World, manager: User, channel_id: str
) -> None:
    seed_video(world, channel_id, "a", at(10), (at(13), 100, 0), (at(14), 160, 0), (at(17), 460, 0))

    points = run(GetChannelDailyViews(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert [p.day.day for p in points] == list(range(13, 20))
    assert [p.views for p in points] == [0, 60, 100, 100, 100, 0, 0]


def test_video_growth_reports_24h_and_72h_views(
    world: World, manager: User, channel_id: str
) -> None:
    seed_video(
        world,
        channel_id,
        "a",
        at(14, 8),
        (at(15, 9), 500, 0),
        (at(17, 7), 1200, 0),
        (at(19), 2000, 0),
    )
    seed_video(world, channel_id, "b", at(18, 8), (at(19, 6), 50, 0))

    items = run(GetVideoGrowth(world.uow, world.clock).execute(manager, channel_id, LAST_7))

    assert [item.platform_video_id for item in items] == ["a", "b"]
    assert (items[0].views_24h, items[0].views_72h, items[0].views) == (500, 1200, 2000)
    assert [(p.age_days, p.views) for p in items[0].curve] == [(1, 500), (2, 1200), (5, 2000)]
    assert (items[1].views_24h, items[1].views_72h) == (50, None)
