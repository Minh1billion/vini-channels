from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode
from vinichannels.domain.syncing.entities import SyncStatus, SyncTrigger


class SyncRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel_id: str
    handle: str
    trigger: SyncTrigger
    status: SyncStatus
    source: str | None
    items_fetched: int
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
    error_code: str | None
    error_message: str | None


class SyncScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    channel_id: str
    handle: str
    display_name: str
    connection_mode: ConnectionMode
    status: ChannelStatus
    is_active: bool
    cron: str
    is_default_cron: bool
    timezone: str
    next_run_at: datetime | None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    enabled: bool
    priority: int
    monthly_quota: int | None
    used_this_month: int
    is_configured: bool
    credential_fields: list[str]
    optional_fields: list[str]
    requires_channel_token: bool


class ProviderUpdateRequest(BaseModel):
    enabled: bool | None = None
    priority: int | None = None
    monthly_quota: int | None = None
    credentials: dict[str, str] | None = None


class CredentialRequest(BaseModel):
    access_token: str
    expires_at: datetime
    refresh_token: str | None = None
