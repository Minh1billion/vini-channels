from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone

from vinichannels.domain.shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date
    offset_minutes: int = 0

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValidationError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")

    @classmethod
    def last_days(cls, days: int, end: date, offset_minutes: int = 0) -> "DateRange":
        if days < 1:
            raise ValidationError("Số ngày phải lớn hơn 0")
        return cls(end - timedelta(days=days - 1), end, offset_minutes)

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def previous(self) -> "DateRange":
        return DateRange(
            self.start - timedelta(days=self.days),
            self.start - timedelta(days=1),
            self.offset_minutes,
        )

    def bounds(self) -> tuple[datetime, datetime]:
        zone = timezone(timedelta(minutes=self.offset_minutes))
        since = datetime.combine(self.start, time.min, zone).astimezone(UTC)
        until = datetime.combine(self.end + timedelta(days=1), time.min, zone).astimezone(UTC)
        return since, until

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True, slots=True)
class PeriodSpec:
    days: int = 30
    start: date | None = None
    end: date | None = None
    all_time: bool = False
    offset_minutes: int = 0

    @classmethod
    def last(cls, days: int, offset_minutes: int = 0) -> "PeriodSpec":
        if days < 1:
            raise ValidationError("Số ngày phải lớn hơn 0")
        return cls(days=days, offset_minutes=offset_minutes)

    @classmethod
    def between(cls, start: date, end: date, offset_minutes: int = 0) -> "PeriodSpec":
        DateRange(start, end)
        return cls(start=start, end=end, offset_minutes=offset_minutes)

    @classmethod
    def everything(cls, offset_minutes: int = 0) -> "PeriodSpec":
        return cls(all_time=True, offset_minutes=offset_minutes)

    @property
    def label(self) -> str:
        if self.all_time:
            return "all"
        if self.start is not None and self.end is not None:
            return f"{self.start}..{self.end}"
        return f"{self.days}d"

    def resolve(self, now: datetime, earliest: datetime | None = None) -> DateRange:
        zone = timezone(timedelta(minutes=self.offset_minutes))
        today = now.astimezone(zone).date()
        if self.start is not None and self.end is not None:
            end = max(self.start, min(self.end, today))
            return DateRange(self.start, end, self.offset_minutes)
        if self.all_time:
            first = earliest.astimezone(zone).date() if earliest else today
            return DateRange(min(first, today), today, self.offset_minutes)
        return DateRange.last_days(self.days, today, self.offset_minutes)
