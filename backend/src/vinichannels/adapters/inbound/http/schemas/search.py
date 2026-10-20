from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vinichannels.adapters.inbound.http.schemas.channels import ChannelResponse
from vinichannels.adapters.inbound.http.schemas.partners import PartnerResponse


class SearchVideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    handle: str
    caption: str
    thumbnail_url: str | None
    posted_at: datetime


class SearchResponse(BaseModel):
    partners: list[PartnerResponse]
    channels: list[ChannelResponse]
    videos: list[SearchVideoResponse]
