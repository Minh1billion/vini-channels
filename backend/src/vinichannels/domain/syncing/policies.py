from dataclasses import dataclass
from enum import StrEnum

from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.syncing.entities import SyncStatus


class SyncErrorKind(StrEnum):
    NETWORK = "network"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    TOKEN_REVOKED = "token_revoked"
    NOT_FOUND = "not_found"
    PRIVATE = "private"

    @property
    def is_transient(self) -> bool:
        return self in {
            SyncErrorKind.NETWORK,
            SyncErrorKind.RATE_LIMITED,
            SyncErrorKind.SERVER_ERROR,
        }

    @property
    def resulting_channel_status(self) -> ChannelStatus | None:
        return {
            SyncErrorKind.TOKEN_REVOKED: ChannelStatus.TOKEN_REVOKED,
            SyncErrorKind.NOT_FOUND: ChannelStatus.NOT_FOUND,
            SyncErrorKind.PRIVATE: ChannelStatus.PRIVATE,
        }.get(self)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_sec: float = 30.0
    factor: float = 2.0
    max_delay_sec: float = 900.0

    def should_retry(self, attempt: int, kind: SyncErrorKind) -> bool:
        return kind.is_transient and attempt < self.max_attempts

    def delay_for(self, attempt: int) -> float:
        if attempt < 1:
            return 0.0
        return min(self.base_delay_sec * self.factor ** (attempt - 1), self.max_delay_sec)


@dataclass(frozen=True, slots=True)
class FastPollPolicy:
    window_hours: float = 72.0

    def interval_minutes(self, video_age_hours: float) -> int | None:
        if video_age_hours < 0 or video_age_hours >= self.window_hours:
            return None
        if video_age_hours < 6:
            return 15
        if video_age_hours < 24:
            return 60
        return 180


def has_consecutive_failures(history: list[SyncStatus], threshold: int = 3) -> bool:
    if threshold < 1 or len(history) < threshold:
        return False
    return all(status is SyncStatus.FAILED for status in history[-threshold:])
