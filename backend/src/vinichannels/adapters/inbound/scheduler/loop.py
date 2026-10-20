import asyncio
import contextlib
import logging
from typing import Protocol

from vinichannels.application.use_cases.syncing.scheduled import DueSyncReport

_log = logging.getLogger(__name__)


class DueSyncRunner(Protocol):
    async def execute(self) -> DueSyncReport: ...


class SchedulerLoop:
    def __init__(self, runner: DueSyncRunner, interval_sec: float) -> None:
        self._runner = runner
        self._interval = max(0.01, interval_sec)

    async def tick(self) -> DueSyncReport | None:
        try:
            report = await self._runner.execute()
        except Exception:
            _log.exception("Vòng lập lịch đồng bộ thất bại")
            return None
        if (
            report.due
            or report.invalid_schedules
            or report.tokens_refreshed
            or report.tokens_revoked
            or report.token_failures
        ):
            _log.info(
                "Đồng bộ theo lịch: đến hạn=%d thành công=%d thất bại=%d bỏ qua=%d lịch lỗi=%d "
                "token: gia hạn=%d thu hồi=%d lỗi=%d",
                report.due,
                report.succeeded,
                report.failed,
                report.skipped,
                report.invalid_schedules,
                report.tokens_refreshed,
                report.tokens_revoked,
                report.token_failures,
            )
        return report

    async def run_forever(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await self.tick()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), self._interval)
