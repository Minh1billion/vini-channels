from datetime import UTC, date, datetime

from vinichannels.domain.analytics.periods import DateRange
from vinichannels.domain.analytics.views import daily_views, growth_curve
from vinichannels.domain.content.snapshots import VideoSnapshot
from vinichannels.domain.shared.ids import VideoId


def snap(day: int, views: int, hour: int = 8) -> VideoSnapshot:
    return VideoSnapshot(VideoId("v"), datetime(2026, 10, day, hour, tzinfo=UTC), "apify", views, 0, 0, 0)


PERIOD = DateRange(date(2026, 10, 13), date(2026, 10, 19))


def test_daily_views_from_cumulative_differences() -> None:
    result = daily_views([[snap(13, 100), snap(14, 150), snap(15, 400)]], PERIOD)

    assert result[date(2026, 10, 13)] == 0
    assert result[date(2026, 10, 14)] == 50
    assert result[date(2026, 10, 15)] == 250


def test_daily_views_spreads_gap_across_missing_days() -> None:
    result = daily_views([[snap(13, 100), snap(17, 500)]], PERIOD)

    assert [result[date(2026, 10, day)] for day in (14, 15, 16, 17)] == [100, 100, 100, 100]
    assert result[date(2026, 10, 18)] == 0


def test_daily_views_sums_videos_and_ignores_decreases() -> None:
    other = [snap(13, 50), snap(14, 40)]

    result = daily_views([[snap(13, 100), snap(14, 130)], other], PERIOD)

    assert result[date(2026, 10, 14)] == 30


def test_daily_views_uses_baseline_before_period_and_clips() -> None:
    result = daily_views([[snap(11, 100), snap(14, 400), snap(21, 700)]], PERIOD)

    assert result[date(2026, 10, 13)] == 100
    assert result[date(2026, 10, 14)] == 100
    assert result[date(2026, 10, 19)] == 42
    assert sum(result.values()) == 410


def test_growth_curve_takes_last_snapshot_per_age_and_skips_gaps() -> None:
    posted = datetime(2026, 10, 13, 8, tzinfo=UTC)

    curve = growth_curve([snap(13, 10, 9), snap(13, 20, 20), snap(14, 90), snap(17, 300)], posted, 7)

    assert curve == [(0, 20), (1, 90), (4, 300)]
