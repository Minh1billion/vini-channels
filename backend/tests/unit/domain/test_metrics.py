from datetime import date, datetime, timedelta

import pytest

from vinichannels.domain.analytics import metrics
from vinichannels.domain.analytics.periods import DateRange
from vinichannels.domain.content.snapshots import VideoSnapshot
from vinichannels.domain.shared.ids import VideoId


def test_division_by_zero_returns_none() -> None:
    assert metrics.safe_div(1, 0) is None
    assert metrics.engagement_rate_by_views(1, 1, 1, 0) is None
    assert metrics.reach_ratio(100.0, 0) is None
    assert metrics.change_ratio(10, 0) is None
    assert metrics.change_ratio(None, 5) is None


def test_engagement_rate_by_views() -> None:
    assert metrics.engagement_rate_by_views(50, 5, 5, 1000) == pytest.approx(0.06)


def test_growth_absolute_and_ratio() -> None:
    assert metrics.growth(1000, 1100) == (100, pytest.approx(0.1))
    assert metrics.growth(0, 50) == (50, None)
    assert metrics.growth(1000, 900) == (-100, pytest.approx(-0.1))


def test_median_is_robust_to_outliers() -> None:
    assert metrics.median([100, 120, 110, 10_000_000]) == 115
    assert metrics.median([]) is None


def test_viral_rate_uses_multiple_of_median() -> None:
    views = [100, 100, 100, 100, 400]
    assert metrics.viral_rate(views) == pytest.approx(0.2)
    assert metrics.viral_rate(views, multiplier=5) == 0
    assert metrics.viral_rate([]) is None
    assert metrics.viral_rate([0, 0, 0]) is None


def test_posts_per_week() -> None:
    period = DateRange(date(2026, 10, 1), date(2026, 10, 14))
    assert metrics.posts_per_week(10, period) == pytest.approx(5)


def test_pooled_rate_is_not_average_of_rates() -> None:
    small = (50, 100)
    large = (1000, 100_000)
    pooled = metrics.pooled_engagement_rate([small, large])
    naive = (50 / 100 + 1000 / 100_000) / 2
    assert pooled == pytest.approx(1050 / 100_100)
    assert pooled != pytest.approx(naive)
    assert metrics.pooled_engagement_rate([]) is None


def test_contribution_shares() -> None:
    shares = metrics.contribution_shares({"a": 75, "b": 25})
    assert shares == {"a": 0.75, "b": 0.25}
    assert metrics.contribution_shares({"a": 0}) == {"a": None}


def make_snapshot(at: datetime, views: int) -> VideoSnapshot:
    return VideoSnapshot(VideoId("v1"), at, "fake", views=views, likes=0, comments=0, shares=0)


def test_views_at_age_picks_closest_within_tolerance(now: datetime) -> None:
    posted = now
    snapshots = [
        make_snapshot(posted + timedelta(hours=1), 100),
        make_snapshot(posted + timedelta(hours=23), 900),
        make_snapshot(posted + timedelta(hours=26), 1100),
    ]
    assert metrics.views_at_age(snapshots, posted, timedelta(hours=24)) == 900
    assert metrics.views_at_age(snapshots, posted, timedelta(hours=72)) is None
    assert metrics.views_at_age([], posted, timedelta(hours=24)) is None


def test_compute_channel_metrics() -> None:
    videos = [
        metrics.VideoStats(views=1000, likes=60, comments=10, shares=10),
        metrics.VideoStats(views=1000, likes=40, comments=0, shares=0),
        metrics.VideoStats(views=4000, likes=200, comments=20, shares=20),
    ]
    period = DateRange(date(2026, 10, 1), date(2026, 10, 7))
    result = metrics.compute_channel_metrics(videos, 10_000, 11_000, period)
    assert result.video_count == 3
    assert result.total_views == 6000
    assert result.average_views == 2000
    assert result.median_views == 1000
    assert result.erv == pytest.approx(360 / 6000)
    assert result.erf == pytest.approx((360 / 3) / 11_000)
    assert result.reach_ratio == pytest.approx(2000 / 11_000)
    assert result.like_rate == pytest.approx(300 / 6000)
    assert result.viral_rate == pytest.approx(1 / 3)
    assert result.posts_per_week == pytest.approx(3)
    assert result.follower_growth == 1000
    assert result.follower_growth_ratio == pytest.approx(0.1)


def test_compute_channel_metrics_with_no_videos() -> None:
    period = DateRange(date(2026, 10, 1), date(2026, 10, 7))
    result = metrics.compute_channel_metrics([], 0, 0, period)
    assert result.video_count == 0
    assert result.erv is None
    assert result.average_views is None
    assert result.viral_rate is None
    assert result.follower_growth_ratio is None
    assert result.posts_per_week == 0
