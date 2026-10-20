from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vinichannels.domain.shared.errors import InvalidStateError
from vinichannels.domain.shared.ids import ChannelId, SyncRunId
from vinichannels.domain.shared.time import require_aware


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SyncTrigger(StrEnum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"


@dataclass(slots=True)
class SyncRun:
    id: SyncRunId
    channel_id: ChannelId
    scheduled_for: datetime
    trigger: SyncTrigger
    started_at: datetime
    status: SyncStatus = SyncStatus.RUNNING
    finished_at: datetime | None = None
    source: str | None = None
    items_fetched: int = 0
    error_code: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        require_aware(self.scheduled_for, "scheduled_for")
        require_aware(self.started_at, "started_at")

    @property
    def is_finished(self) -> bool:
        return self.status is not SyncStatus.RUNNING

    @property
    def duration_sec(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    def _finish(self, status: SyncStatus, at: datetime) -> None:
        if self.is_finished:
            raise InvalidStateError("Lần đồng bộ đã kết thúc")
        require_aware(at, "finished_at")
        self.status = status
        self.finished_at = at

    def succeed(self, at: datetime, source: str, items: int) -> None:
        self._finish(SyncStatus.SUCCESS, at)
        self.source = source
        self.items_fetched = items

    def partially_succeed(
        self, at: datetime, source: str, items: int, code: str, message: str
    ) -> None:
        self._finish(SyncStatus.PARTIAL, at)
        self.source = source
        self.items_fetched = items
        self.error_code = code
        self.error_message = message

    def fail(self, at: datetime, code: str, message: str, source: str | None = None) -> None:
        self._finish(SyncStatus.FAILED, at)
        self.source = source
        self.error_code = code
        self.error_message = message
