from dataclasses import dataclass, field
from datetime import datetime, timedelta

from vinichannels.domain.channels.events import ChannelStatusChanged
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode, Handle
from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import ChannelId, PartnerId
from vinichannels.domain.shared.time import require_aware

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"


@dataclass(slots=True)
class Channel:
    id: ChannelId
    partner_id: PartnerId
    handle: Handle
    display_name: str
    connection_mode: ConnectionMode = ConnectionMode.PUBLIC
    status: ChannelStatus = ChannelStatus.HEALTHY
    platform_channel_id: str | None = None
    avatar_url: str | None = None
    sync_cron: str | None = None
    timezone: str = DEFAULT_TIMEZONE
    is_active: bool = True
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.display_name = self.display_name.strip() or self.handle.display

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def change_status(self, status: ChannelStatus, at: datetime) -> ChannelStatusChanged | None:
        if status == self.status:
            return None
        previous = self.status
        self.status = status
        return ChannelStatusChanged(
            occurred_at=at, channel_id=self.id, previous=previous, current=status
        )

    def authorize(self, at: datetime) -> ChannelStatusChanged | None:
        self.connection_mode = ConnectionMode.AUTHORIZED
        return self.change_status(ChannelStatus.HEALTHY, at)

    def revoke(self, at: datetime) -> ChannelStatusChanged | None:
        if self.connection_mode is not ConnectionMode.AUTHORIZED:
            raise InvalidStateError("Kênh công khai không có quyền để thu hồi")
        return self.change_status(ChannelStatus.TOKEN_REVOKED, at)

    def set_schedule(self, cron: str | None, timezone: str) -> None:
        self.sync_cron = cron
        self.timezone = timezone

    def archive(self, at: datetime) -> None:
        if self.is_archived:
            raise InvalidStateError("Kênh đã được lưu trữ")
        self.archived_at = at
        self.is_active = False

    def restore(self) -> None:
        if not self.is_archived:
            raise InvalidStateError("Kênh chưa được lưu trữ")
        self.archived_at = None
        self.is_active = True

    @property
    def is_syncable(self) -> bool:
        if not self.is_active or self.is_archived:
            return False
        return self.status not in {ChannelStatus.TOKEN_REVOKED, ChannelStatus.NOT_FOUND}


@dataclass(frozen=True, slots=True)
class ChannelCredential:
    channel_id: ChannelId
    access_token_enc: bytes
    refresh_token_enc: bytes
    expires_at: datetime
    refresh_expires_at: datetime | None = None
    scopes: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        require_aware(self.expires_at, "expires_at")
        if self.refresh_expires_at is not None:
            require_aware(self.refresh_expires_at, "refresh_expires_at")
        if not self.access_token_enc:
            raise ValidationError("Token truy cập không được để trống")

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now

    def expires_within(self, now: datetime, window: timedelta) -> bool:
        return self.expires_at - now <= window

    def can_refresh(self, now: datetime) -> bool:
        return self.refresh_expires_at is None or self.refresh_expires_at > now
