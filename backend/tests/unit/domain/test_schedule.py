from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.syncing.schedule import CronExpression, SchedulePreset, SyncSchedule


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "* * * *",
        "60 * * * *",
        "* 24 * * *",
        "* * 0 * *",
        "* * * 13 *",
        "a * * * *",
        "*/0 * * * *",
    ],
)
def test_invalid_cron_is_rejected(expression: str) -> None:
    with pytest.raises(ValidationError):
        CronExpression.parse(expression)


def test_unknown_timezone_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SyncSchedule.from_cron("0 * * * *", "Mars/Olympus")


def test_every_six_hours_in_ho_chi_minh() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.EVERY_6_HOURS)
    assert schedule.next_run_after(utc(2026, 10, 19, 7, 0)) == utc(2026, 10, 19, 11, 0)
    assert schedule.next_run_after(utc(2026, 10, 19, 11, 0)) == utc(2026, 10, 19, 17, 0)


def test_daily_at_eight_local_is_one_utc() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.DAILY)
    assert schedule.next_run_after(utc(2026, 10, 19, 7, 0)) == utc(2026, 10, 20, 1, 0)


def test_weekly_runs_on_monday() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.WEEKLY)
    assert schedule.next_run_after(utc(2026, 10, 19, 2, 0)) == utc(2026, 10, 26, 1, 0)
    assert utc(2026, 10, 26, 1, 0).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).weekday() == 0


def test_steps_ranges_and_lists() -> None:
    schedule = SyncSchedule.from_cron("5,35 9-10 * * 1-5", "UTC")
    assert schedule.next_run_after(utc(2026, 10, 19, 9, 5)) == utc(2026, 10, 19, 9, 35)
    assert schedule.next_run_after(utc(2026, 10, 19, 10, 35)) == utc(2026, 10, 20, 9, 5)
    assert schedule.next_run_after(utc(2026, 10, 23, 10, 35)) == utc(2026, 10, 26, 9, 5)


def test_sunday_accepts_zero_and_seven() -> None:
    zero = CronExpression.parse("0 0 * * 0")
    seven = CronExpression.parse("0 0 * * 7")
    assert zero.days_of_week == seven.days_of_week == frozenset({0})


def test_day_of_month_and_weekday_are_or_when_both_restricted() -> None:
    schedule = SyncSchedule.from_cron("0 0 1 * 1", "UTC")
    assert schedule.next_run_after(utc(2026, 10, 19, 0, 0)) == utc(2026, 10, 26, 0, 0)
    assert schedule.next_run_after(utc(2026, 10, 27, 0, 0)) == utc(2026, 11, 1, 0, 0)


def test_impossible_date_raises() -> None:
    with pytest.raises(ValidationError):
        SyncSchedule.from_cron("0 0 31 2 *", "UTC").next_run_after(utc(2026, 1, 1))


def test_naive_datetime_is_rejected() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.DAILY)
    with pytest.raises(ValidationError):
        schedule.next_run_after(datetime(2026, 10, 19, 7, 0))


def test_first_sync_is_due_immediately(now: datetime) -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.DAILY)
    assert schedule.pending_slot(None, now) == now


def test_slot_not_due_before_next_run() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.EVERY_6_HOURS)
    last = utc(2026, 10, 19, 5, 0)
    assert schedule.pending_slot(last, last + timedelta(hours=5, minutes=59)) is None


def test_slot_due_exactly_at_next_run() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.EVERY_6_HOURS)
    last = utc(2026, 10, 19, 5, 0)
    assert schedule.pending_slot(last, utc(2026, 10, 19, 11, 0)) == utc(2026, 10, 19, 11, 0)


def test_missed_slots_collapse_to_latest() -> None:
    schedule = SyncSchedule.from_preset(SchedulePreset.EVERY_6_HOURS)
    last = utc(2026, 10, 18, 5, 0)
    assert schedule.pending_slot(last, utc(2026, 10, 19, 12, 30)) == utc(2026, 10, 19, 11, 0)
