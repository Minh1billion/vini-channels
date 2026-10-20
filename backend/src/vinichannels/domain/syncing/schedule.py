from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from vinichannels.domain.channels.entities import DEFAULT_TIMEZONE
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.time import require_aware

_MAX_SEARCH_YEARS = 8


class SchedulePreset(StrEnum):
    EVERY_6_HOURS = "0 */6 * * *"
    EVERY_12_HOURS = "0 */12 * * *"
    DAILY = "0 8 * * *"
    WEEKLY = "0 8 * * 1"


def _parse_field(text: str, low: int, high: int) -> tuple[frozenset[int], bool]:
    values: set[int] = set()
    for item in text.split(","):
        if not item:
            raise ValidationError(f"Biểu thức cron không hợp lệ: {text!r}")
        base, _, step_text = item.partition("/")
        step = 1
        if step_text:
            if not step_text.isdigit() or int(step_text) < 1:
                raise ValidationError(f"Bước cron không hợp lệ: {item!r}")
            step = int(step_text)
        if base == "*":
            start, end = low, high
        elif "-" in base:
            left, _, right = base.partition("-")
            if not (left.isdigit() and right.isdigit()):
                raise ValidationError(f"Khoảng cron không hợp lệ: {item!r}")
            start, end = int(left), int(right)
        elif base.isdigit():
            start = int(base)
            end = high if step_text else start
        else:
            raise ValidationError(f"Giá trị cron không hợp lệ: {item!r}")
        if start < low or end > high or start > end:
            raise ValidationError(f"Giá trị cron ngoài phạm vi {low}-{high}: {item!r}")
        values.update(range(start, end + 1, step))
    return frozenset(values), text.startswith("*")


@dataclass(frozen=True, slots=True)
class CronExpression:
    raw: str
    minutes: frozenset[int]
    hours: frozenset[int]
    days_of_month: frozenset[int]
    months: frozenset[int]
    days_of_week: frozenset[int]
    any_day_of_month: bool
    any_day_of_week: bool

    @classmethod
    def parse(cls, expression: str) -> "CronExpression":
        parts = expression.split()
        if len(parts) != 5:
            raise ValidationError("Biểu thức cron cần đúng 5 trường")
        minutes, _ = _parse_field(parts[0], 0, 59)
        hours, _ = _parse_field(parts[1], 0, 23)
        days_of_month, any_dom = _parse_field(parts[2], 1, 31)
        months, _ = _parse_field(parts[3], 1, 12)
        raw_weekdays, any_dow = _parse_field(parts[4], 0, 7)
        weekdays = frozenset(day % 7 for day in raw_weekdays)
        return cls(
            raw=" ".join(parts),
            minutes=minutes,
            hours=hours,
            days_of_month=days_of_month,
            months=months,
            days_of_week=weekdays,
            any_day_of_month=any_dom,
            any_day_of_week=any_dow,
        )

    def _day_matches(self, moment: datetime) -> bool:
        in_month = moment.day in self.days_of_month
        in_week = (moment.weekday() + 1) % 7 in self.days_of_week
        if self.any_day_of_month and self.any_day_of_week:
            return True
        if self.any_day_of_month:
            return in_week
        if self.any_day_of_week:
            return in_month
        return in_month or in_week

    def next_after(self, moment: datetime) -> datetime:
        current = moment.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = current + timedelta(days=366 * _MAX_SEARCH_YEARS)
        while current <= limit:
            if current.month not in self.months:
                current = (current.replace(day=1, hour=0, minute=0) + timedelta(days=32)).replace(
                    day=1
                )
            elif not self._day_matches(current):
                current = current.replace(hour=0, minute=0) + timedelta(days=1)
            elif current.hour not in self.hours:
                current = current.replace(minute=0) + timedelta(hours=1)
            elif current.minute not in self.minutes:
                current += timedelta(minutes=1)
            else:
                return current
        raise ValidationError("Biểu thức cron không bao giờ khớp")


@dataclass(frozen=True, slots=True)
class SyncSchedule:
    cron: CronExpression
    timezone: str = DEFAULT_TIMEZONE

    def __post_init__(self) -> None:
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValidationError(f"Múi giờ không hợp lệ: {self.timezone!r}") from error

    @classmethod
    def from_cron(cls, expression: str, timezone: str = DEFAULT_TIMEZONE) -> "SyncSchedule":
        return cls(CronExpression.parse(expression), timezone)

    @classmethod
    def from_preset(
        cls, preset: SchedulePreset, timezone: str = DEFAULT_TIMEZONE
    ) -> "SyncSchedule":
        return cls.from_cron(preset.value, timezone)

    def next_run_after(self, moment: datetime) -> datetime:
        zone = ZoneInfo(self.timezone)
        local = require_aware(moment, "moment").astimezone(zone)
        return self.cron.next_after(local).astimezone(UTC)

    def pending_slot(
        self, last_slot: datetime | None, now: datetime, max_steps: int = 10_000
    ) -> datetime | None:
        current = require_aware(now, "now")
        if last_slot is None:
            return current.replace(second=0, microsecond=0)
        slot: datetime | None = None
        cursor = self.next_run_after(last_slot)
        steps = 0
        while cursor <= current and steps < max_steps:
            slot = cursor
            cursor = self.next_run_after(cursor)
            steps += 1
        return slot
