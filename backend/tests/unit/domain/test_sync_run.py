from datetime import datetime, timedelta

import pytest

from vinichannels.domain.shared.errors import InvalidStateError
from vinichannels.domain.shared.ids import ChannelId, SyncRunId
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus, SyncTrigger


def make_run(now: datetime) -> SyncRun:
    return SyncRun(
        id=SyncRunId("r1"),
        channel_id=ChannelId("c1"),
        scheduled_for=now,
        trigger=SyncTrigger.SCHEDULED,
        started_at=now,
    )


def test_new_run_is_running(now: datetime) -> None:
    run = make_run(now)
    assert run.status is SyncStatus.RUNNING
    assert not run.is_finished
    assert run.duration_sec is None


def test_succeed_records_outcome(now: datetime) -> None:
    run = make_run(now)
    run.succeed(now + timedelta(seconds=12), source="fake", items=48)
    assert run.status is SyncStatus.SUCCESS
    assert run.items_fetched == 48
    assert run.duration_sec == 12


def test_fail_records_error(now: datetime) -> None:
    run = make_run(now)
    run.fail(now + timedelta(seconds=3), code="rate_limited", message="429", source="apify")
    assert run.status is SyncStatus.FAILED
    assert run.error_code == "rate_limited"
    assert run.source == "apify"


def test_partial_keeps_items_and_error(now: datetime) -> None:
    run = make_run(now)
    run.partially_succeed(now + timedelta(seconds=9), "apify", 21, "missing_stats", "thiếu số liệu")
    assert run.status is SyncStatus.PARTIAL
    assert run.items_fetched == 21
    assert run.error_code == "missing_stats"


def test_cannot_finish_twice(now: datetime) -> None:
    run = make_run(now)
    run.succeed(now + timedelta(seconds=1), "fake", 1)
    with pytest.raises(InvalidStateError):
        run.fail(now + timedelta(seconds=2), "x", "y")
