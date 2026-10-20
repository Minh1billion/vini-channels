from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PartnerCreateRequest(BaseModel):
    name: str
    industry: str | None = None
    owner_user_id: str | None = None
    logo_url: str | None = None
    notes: str = ""
    tags: list[str] = Field(default_factory=list)


class PartnerUpdateRequest(BaseModel):
    name: str | None = None
    industry: str | None = None
    owner_user_id: str | None = None
    logo_url: str | None = None
    notes: str | None = None
    tags: list[str] | None = None


class PartnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    industry: str | None
    owner_user_id: str | None
    logo_url: str | None
    notes: str
    tags: list[str]
    archived_at: datetime | None
    channel_count: int
