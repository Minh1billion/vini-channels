import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from vinichannels.adapters.inbound.scheduler.loop import SchedulerLoop
from vinichannels.application.use_cases.syncing.scheduled import DueSyncReport


class CountingRunner:
    def __init__(self, stop: asyncio.Event | None = None, stop_after: int = 0) -> None:
        self.calls = 0
        self._stop = stop
        self._stop_after = stop_after

    async def execute(self) -> DueSyncReport:
        self.calls += 1
        if self._stop is not None and self.calls >= self._stop_after:
            self._stop.set()
        return DueSyncReport(due=1, succeeded=1)


class ExplodingRunner:
    async def execute(self) -> DueSyncReport:
        raise RuntimeError("db down")


def test_tick_returns_report() -> None:
    loop = SchedulerLoop(CountingRunner(), 1.0)
    assert asyncio.run(loop.tick()) == DueSyncReport(due=1, succeeded=1)


def test_tick_swallows_unexpected_errors() -> None:
    loop = SchedulerLoop(ExplodingRunner(), 1.0)
    assert asyncio.run(loop.tick()) is None


def test_run_forever_keeps_ticking_until_stopped() -> None:
    async def scenario() -> int:
        stop = asyncio.Event()
        runner = CountingRunner(stop, stop_after=3)
        await asyncio.wait_for(SchedulerLoop(runner, 0.01).run_forever(stop), 5)
        return runner.calls

    assert asyncio.run(scenario()) == 3


def test_run_forever_survives_failing_ticks() -> None:
    async def scenario() -> bool:
        stop = asyncio.Event()
        task = asyncio.create_task(SchedulerLoop(ExplodingRunner(), 0.01).run_forever(stop))
        await asyncio.sleep(0.05)
        alive = not task.done()
        stop.set()
        await asyncio.wait_for(task, 5)
        return alive

    assert asyncio.run(scenario()) is True
