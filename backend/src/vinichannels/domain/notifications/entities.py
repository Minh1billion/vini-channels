from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vinichannels.domain.shared.ids import ChannelId
from vinichannels.domain.shared.time import require_aware


class NotificationKind(StrEnum):
    SYNC_FAILURES = "sync_failures"
    TOKEN_EXPIRING = "token_expiring"
    ENGAGEMENT_DROP = "engagement_drop"


@dataclass(slots=True)
class Notification:
    id: str
    kind: NotificationKind
    channel_id: ChannelId
    dedupe_key: str
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None = None

    def __post_init__(self) -> None:
        require_aware(self.created_at, "created_at")

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self, at: datetime) -> None:
        require_aware(at, "read_at")
        if self.read_at is None:
            self.read_at = at
