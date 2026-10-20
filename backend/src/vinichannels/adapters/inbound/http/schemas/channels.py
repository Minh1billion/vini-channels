from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vinichannels.adapters.inbound.http.schemas.sync import CredentialRequest
from vinichannels.domain.channels.entities import DEFAULT_TIMEZONE
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode


class ChannelCreateRequest(BaseModel):
    partner_id: str
    handle: str
    provider: str
    display_name: str = ""
    sync_cron: str | None = None
    timezone: str = DEFAULT_TIMEZONE
    token: CredentialRequest | None = None


class ChannelUpdateRequest(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None


class ScheduleRequest(BaseModel):
    cron: str | None = None
    timezone: str = DEFAULT_TIMEZONE


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    handle: str
    display_name: str
    avatar_url: str | None
    connection_mode: ConnectionMode
    status: ChannelStatus
    sync_cron: str | None
    timezone: str
    is_active: bool
    archived_at: datetime | None
