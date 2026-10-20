from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

MAX_DETAIL_LENGTH = 200


class AuditAction(StrEnum):
    PARTNER_CREATE = "partner.create"
    PARTNER_UPDATE = "partner.update"
    PARTNER_ARCHIVE = "partner.archive"
    PARTNER_RESTORE = "partner.restore"
    CHANNEL_REGISTER = "channel.register"
    CHANNEL_UPDATE = "channel.update"
    CHANNEL_SCHEDULE = "channel.schedule"
    CHANNEL_ARCHIVE = "channel.archive"
    CHANNEL_RESTORE = "channel.restore"
    CHANNEL_TOKEN = "channel.token"
    CHANNEL_TOKEN_REVOKED = "channel.token_revoked"
    PROVIDER_UPDATE = "provider.update"
    SCORING_WEIGHTS = "scoring.weights"
    USER_CREATE = "user.create"
    USER_ROLE = "user.role"
    USER_STATUS = "user.status"
    USER_PASSWORD = "user.password"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    id: str
    actor_id: str
    actor_email: str
    action: AuditAction
    target_type: str
    target_id: str
    target_label: str
    detail: dict[str, str]
    occurred_at: datetime

    def __post_init__(self) -> None:
        clipped = {name: value[:MAX_DETAIL_LENGTH] for name, value in self.detail.items()}
        object.__setattr__(self, "detail", clipped)
