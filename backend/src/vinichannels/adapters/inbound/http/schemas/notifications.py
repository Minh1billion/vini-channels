from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    channel_id: str
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int


class PushConfigResponse(BaseModel):
    enabled: bool
    public_key: str | None


class PushSubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=1024)
    p256dh: str = Field(min_length=1, max_length=128)
    auth: str = Field(min_length=1, max_length=64)


class PushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=1024)
