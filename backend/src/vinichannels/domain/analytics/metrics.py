from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median as _median

from vinichannels.domain.analytics.periods import DateRange
from vinichannels.domain.content.snapshots import VideoSnapshot

DEFAULT_VIRAL_MULTIPLIER = 3.0


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def change_ratio(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return safe_div(current - previous, previous)


def growth(first: int, last: int) -> tuple[int, float | None]:
    return last - first, safe_div(last - first, first)


def median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return float(_median(values))


def mean(values: Sequence[float]) -> float | None:
    return safe_div(sum(values), len(values))


def engagement_rate_by_views(likes: int, comments: int, shares: int, views: int) -> float | None:
    return safe_div(likes + comments + shares, views)


def engagement_rate_by_followers(
    average_engagement_per_video: float | None, followers: int
) -> float | None:
    if average_engagement_per_video is None:
        return None
    return safe_div(average_engagement_per_video, followers)


def reach_ratio(average_views: float | None, followers: int) -> float | None:
    if average_views is None:
        return None
    return safe_div(average_views, followers)


def viral_rate(views: Sequence[int], multiplier: float = DEFAULT_VIRAL_MULTIPLIER) -> float | None:
    typical = median([float(v) for v in views])
    if typical is None or typical == 0:
        return None
    threshold = multiplier * typical
    return sum(1 for v in views if v >= threshold) / len(views)


def posts_per_week(video_count: int, period: DateRange) -> float | None:
    return safe_div(video_count * 7, period.days)


def pooled_engagement_rate(items: Iterable[tuple[int, int]]) -> float | None:
    total_engagement = 0
    total_views = 0
    for engagement, views in items:
        total_engagement += engagement
        total_views += views
    return safe_div(total_engagement, total_views)


def contribution_shares(values: dict[str, int]) -> dict[str, float | None]:
    total = sum(values.values())
    return {key: safe_div(value, total) for key, value in values.items()}


def views_at_age(
    snapshots: Sequence[VideoSnapshot],
    posted_at: datetime,
    age: timedelta,
    tolerance: timedelta = timedelta(hours=6),
) -> int | None:
    target = posted_at + age
    best: VideoSnapshot | None = None
    best_gap: timedelta | None = None
    for snapshot in snapshots:
        gap = abs(snapshot.captured_at - target)
        if gap <= tolerance and (best_gap is None or gap < best_gap):
            best, best_gap = snapshot, gap
    return best.views if best else None


@dataclass(frozen=True, slots=True)
class VideoStats:
    views: int
    likes: int
    comments: int
    shares: int
    saves: int | None = None

    @property
    def engagements(self) -> int:
        return self.likes + self.comments + self.shares


@dataclass(frozen=True, slots=True)
class ChannelMetrics:
    video_count: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    average_views: float | None
    median_views: float | None
    erv: float | None
    erf: float | None
    like_rate: float | None
    comment_rate: float | None
    share_rate: float | None
    reach_ratio: float | None
    viral_rate: float | None
    posts_per_week: float | None
    follower_growth: int
    follower_growth_ratio: float | None


def compute_channel_metrics(
    videos: Sequence[VideoStats],
    followers_start: int,
    followers_end: int,
    period: DateRange,
    viral_multiplier: float = DEFAULT_VIRAL_MULTIPLIER,
) -> ChannelMetrics:
    count = len(videos)
    views = sum(v.views for v in videos)
    likes = sum(v.likes for v in videos)
    comments = sum(v.comments for v in videos)
    shares = sum(v.shares for v in videos)
    average_views = safe_div(views, count)
    average_engagement = safe_div(likes + comments + shares, count)
    delta, ratio = growth(followers_start, followers_end)
    return ChannelMetrics(
        video_count=count,
        total_views=views,
        total_likes=likes,
        total_comments=comments,
        total_shares=shares,
        average_views=average_views,
        median_views=median([float(v.views) for v in videos]),
        erv=engagement_rate_by_views(likes, comments, shares, views),
        erf=engagement_rate_by_followers(average_engagement, followers_end),
        like_rate=safe_div(likes, views),
        comment_rate=safe_div(comments, views),
        share_rate=safe_div(shares, views),
        reach_ratio=reach_ratio(average_views, followers_end),
        viral_rate=viral_rate([v.views for v in videos], viral_multiplier),
        posts_per_week=posts_per_week(count, period),
        follower_growth=delta,
        follower_growth_ratio=ratio,
    )
