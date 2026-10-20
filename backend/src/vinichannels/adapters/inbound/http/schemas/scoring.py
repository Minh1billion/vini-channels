from datetime import date

from pydantic import BaseModel, ConfigDict


class WeightsRequest(BaseModel):
    engagement: float
    growth: float
    reach: float
    consistency: float


class WeightsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    engagement: float
    growth: float
    reach: float
    consistency: float


class ChannelScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    partner_id: str
    partner_name: str
    handle: str
    display_name: str
    rank: int | None
    total: float | None
    components: dict[str, float | None]
    erv: float | None
    follower_growth_ratio: float | None
    reach_ratio: float | None
    posts_per_week: float | None


class PartnerScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    partner_id: str
    name: str
    rank: int | None
    total: float | None
    channel_count: int
    scored_channel_count: int


class ScoreboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_start: date
    period_end: date
    days: int
    weights: WeightsResponse
    channels: list[ChannelScoreResponse]
    partners: list[PartnerScoreResponse]
