from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date, datetime, timedelta

from vinichannels.domain.analytics.periods import DateRange
from vinichannels.domain.content.snapshots import VideoSnapshot


def _span(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def daily_views(series: Iterable[Sequence[VideoSnapshot]], period: DateRange) -> dict[date, int]:
    totals: dict[date, int] = dict.fromkeys(_span(period.start, period.end), 0)
    for snapshots in series:
        ordered = sorted(snapshots, key=lambda item: item.captured_at)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            delta = max(0, current.views - previous.views)
            last_day = current.captured_at.date()
            first_day = previous.captured_at.date() + timedelta(days=1)
            days = _span(first_day, last_day) if first_day <= last_day else [last_day]
            share, remainder = divmod(delta, len(days))
            for index, day in enumerate(days):
                if day in totals:
                    totals[day] += share + (remainder if index == len(days) - 1 else 0)
    return totals


def growth_curve(
    snapshots: Sequence[VideoSnapshot], posted_at: datetime, max_days: int
) -> list[tuple[int, int]]:
    last_per_age: dict[int, VideoSnapshot] = {}
    for snapshot in sorted(snapshots, key=lambda item: item.captured_at):
        age = (snapshot.captured_at - posted_at).days
        if 0 <= age <= max_days:
            last_per_age[age] = snapshot
    return [(age, last_per_age[age].views) for age in sorted(last_per_age)]


def group_by_video(snapshots: Iterable[VideoSnapshot]) -> dict[str, list[VideoSnapshot]]:
    grouped: dict[str, list[VideoSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        grouped[snapshot.video_id].append(snapshot)
    return grouped
