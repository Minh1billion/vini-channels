from datetime import UTC, date, datetime

import pytest

from vinichannels.domain.analytics.periods import DateRange, PeriodSpec
from vinichannels.domain.shared.errors import ValidationError


def test_last_days_is_inclusive() -> None:
    period = DateRange.last_days(7, date(2026, 10, 19))
    assert period.start == date(2026, 10, 13)
    assert period.days == 7


def test_previous_has_same_length_and_is_adjacent() -> None:
    period = DateRange.last_days(30, date(2026, 10, 19))
    previous = period.previous()
    assert previous.days == 30
    assert previous.end == date(2026, 9, 19)
    assert previous.start == date(2026, 8, 21)


def test_contains_bounds() -> None:
    period = DateRange(date(2026, 10, 1), date(2026, 10, 3))
    assert period.contains(date(2026, 10, 1))
    assert period.contains(date(2026, 10, 3))
    assert not period.contains(date(2026, 10, 4))


def test_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        DateRange(date(2026, 10, 3), date(2026, 10, 1))
    with pytest.raises(ValidationError):
        DateRange.last_days(0, date(2026, 10, 1))


def test_spec_today_follows_offset() -> None:
    now = datetime(2026, 10, 19, 20, 0, tzinfo=UTC)
    assert PeriodSpec.last(1).resolve(now).start == date(2026, 10, 19)
    assert PeriodSpec.last(1, 420).resolve(now).start == date(2026, 10, 20)


def test_spec_custom_clamps_future_end() -> None:
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    period = PeriodSpec.between(date(2026, 10, 10), date(2026, 11, 1)).resolve(now)
    assert period.end == date(2026, 10, 19)


def test_spec_all_time_starts_at_earliest() -> None:
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    earliest = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    period = PeriodSpec.everything().resolve(now, earliest)
    assert (period.start, period.end) == (date(2026, 9, 1), date(2026, 10, 19))


def test_bounds_use_offset() -> None:
    since, _ = DateRange(date(2026, 10, 20), date(2026, 10, 20), 420).bounds()
    assert since == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
