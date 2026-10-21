from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict

from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.shared.errors import ValidationError


def period_spec(
    range_: Annotated[str, Query(alias="range", pattern=r"^([1-9]\d{0,2}d|all)$")] = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    tz_offset: Annotated[int, Query(ge=-840, le=840)] = 0,
) -> PeriodSpec:
    if (date_from is None) != (date_to is None):
        raise ValidationError("Cần cung cấp cả date_from và date_to")
    if date_from is not None and date_to is not None:
        return PeriodSpec.between(date_from, date_to, tz_offset)
    if range_ == "all":
        return PeriodSpec.everything(tz_offset)
    return PeriodSpec.last(int(range_.removesuffix("d")), tz_offset)


PeriodDep = Annotated[PeriodSpec, Depends(period_spec)]


class MetricsValues(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ChannelMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    period_start: date
    period_end: date
    days: int
    current: MetricsValues
    previous: MetricsValues
    erv_change: float | None
    average_views_change: float | None


class DailyViewsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    views: int


class DailyPostsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    count: int


class GrowthPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    age_days: int
    views: int


class VideoGrowthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    video_id: str
    platform_video_id: str
    caption: str
    posted_at: datetime
    views: int
    views_24h: int | None
    views_72h: int | None
    curve: list[GrowthPointResponse]


class CompareResponse(BaseModel):
    range: str
    channels: list[ChannelMetricsResponse]


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    handle: str
    platform_video_id: str
    url: str | None
    caption: str
    thumbnail_url: str | None
    duration_sec: int
    posted_at: datetime
    captured_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: int | None
    erv: float | None


class TrendPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: date
    followers: int
    total_likes: int
    video_count: int


class ChannelOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    followers: int | None
    follower_growth: int
    follower_growth_ratio: float | None
    views: int
    video_count: int
    average_views: float | None
    erv: float | None


class OverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_start: date
    period_end: date
    days: int
    channel_count: int
    followers: int
    follower_growth: int
    views: int
    views_change: float | None
    video_count: int
    video_count_change: float | None
    erv: float | None
    erv_change: float | None
    channels: list[ChannelOverviewResponse]
