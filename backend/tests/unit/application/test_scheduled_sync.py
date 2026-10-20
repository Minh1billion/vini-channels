import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests.unit.application.conftest import World, add_channel, run
from tests.unit.application.support import (
    FakeProvider,
    PlainCipher,
    enable_apify,
    make_data,
    noop_sleep,
)
from vinichannels.application.errors import DuplicateSyncRun
from vinichannels.application.ports.data_provider import FetchRequest, ProviderData, ProviderError
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.application.use_cases.syncing.scheduled import RunDueSyncs
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel
from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.identity.entities import User
from vinichannels.domain.syncing.entities import SyncStatus, SyncTrigger
from vinichannels.domain.syncing.policies import RetryPolicy, SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderKey


class ConcurrencyProbe:
    key = ProviderKey.APIFY.value

    def __init__(self, world: World) -> None:
        self._world = world
        self.active = 0
        self.peak = 0

    async def fetch(self, request: FetchRequest) -> ProviderData:
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.active -= 1
        return make_data(self._world)


class Setup:
    def __init__(self, world: World, manager: User, provider: object, **options: int) -> None:
        self.world = world
        self.manager = manager
        self.partner_id = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha")).id
        self.sync = SyncChannel(
            world.uow,
            {ProviderKey.APIFY.value: provider},  # type: ignore[dict-item]
            PlainCipher(),
            world.clock,
            RetryPolicy(max_attempts=2),
            noop_sleep,
        )
        self.due = RunDueSyncs(world.uow, self.sync, world.clock, **options)
        enable_apify(world)

    def channel(self, handle: str) -> str:
        return add_channel(self.world, self.partner_id, handle).id

    def runs(self, trigger: SyncTrigger = SyncTrigger.SCHEDULED) -> list:  # type: ignore[type-arg]
        return [r for r in self.world.uow.state.sync_runs.values() if r.trigger is trigger]


def _setup(
    world: World, manager: User, *results: ProviderData | Exception, **options: int
) -> Setup:
    provider = FakeProvider(ProviderKey.APIFY.value, *(results or (make_data(world),)))
    return Setup(world, manager, provider, **options)


def test_new_channel_syncs_once_then_waits_for_next_slot(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    setup.channel("alpha.vn")
    first = run(setup.due.execute())
    assert (first.due, first.succeeded) == (1, 1)
    assert run(setup.due.execute()).due == 0
    assert len(setup.runs()) == 1


def test_next_slot_runs_at_local_cron_time(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    setup.channel("alpha.vn")
    run(setup.due.execute())
    world.clock.current = datetime(2026, 10, 20, 1, 30, tzinfo=UTC)
    report = run(setup.due.execute())
    assert report.succeeded == 1
    slots = sorted(r.scheduled_for for r in setup.runs())
    assert slots[-1] == datetime(2026, 10, 20, 1, 0, tzinfo=UTC)


def test_missed_slots_collapse_into_one_catch_up_run(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    setup.channel("alpha.vn")
    run(setup.due.execute())
    world.clock.current += timedelta(days=5)
    report = run(setup.due.execute())
    assert (report.due, report.succeeded) == (1, 1)
    assert len(setup.runs()) == 2
    assert run(setup.due.execute()).due == 0


def test_manual_run_counts_as_last_sync(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    channel_id = setup.channel("alpha.vn")
    run(setup.sync.execute(manager, channel_id))
    assert run(setup.due.execute()).due == 0


def test_inactive_and_blocked_channels_are_skipped(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    archived = setup.channel("archived.vn")
    revoked = setup.channel("revoked.vn")
    paused = setup.channel("paused.vn")
    setup.channel("active.vn")
    state = world.uow.state
    state.channels[archived].archive(world.clock.now())
    state.channels[revoked].status = ChannelStatus.TOKEN_REVOKED
    state.channels[paused].is_active = False
    report = run(setup.due.execute())
    assert report.due == 1
    assert len(setup.runs()) == 1


def test_invalid_schedule_is_counted_not_fatal(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    broken = setup.channel("broken.vn")
    setup.channel("fine.vn")
    world.uow.state.channels[broken].sync_cron = "not a cron"
    report = run(setup.due.execute())
    assert (report.invalid_schedules, report.due, report.succeeded) == (1, 1, 1)


def test_failed_run_still_advances_to_next_slot(world: World, manager: User) -> None:
    down = ProviderError(SyncErrorKind.SERVER_ERROR, "down")
    setup = _setup(world, manager, down)
    setup.channel("alpha.vn")
    report = run(setup.due.execute())
    assert (report.due, report.failed) == (1, 1)
    assert [r.status for r in setup.runs()] == [SyncStatus.FAILED]
    assert run(setup.due.execute()).due == 0


def test_channel_without_ready_provider_is_skipped(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    setup.channel("alpha.vn")
    world.uow.state.providers.clear()
    report = run(setup.due.execute())
    assert (report.due, report.skipped, report.succeeded) == (1, 1, 0)
    assert setup.runs() == []


def test_same_slot_cannot_be_claimed_twice(world: World, manager: User) -> None:
    setup = _setup(world, manager)
    channel_id = setup.channel("alpha.vn")
    slot = datetime(2026, 10, 19, 1, 0, tzinfo=UTC)
    run(setup.sync.run(channel_id, SyncTrigger.SCHEDULED, slot))
    with pytest.raises(DuplicateSyncRun):
        run(setup.sync.run(channel_id, SyncTrigger.SCHEDULED, slot))
    assert len(setup.runs()) == 1


def test_batch_limit_spreads_work_across_ticks(world: World, manager: User) -> None:
    setup = _setup(world, manager, max_batch=2)
    for handle in ("a.vn", "b.vn", "c.vn"):
        setup.channel(handle)
    first = run(setup.due.execute())
    assert (first.due, first.succeeded) == (3, 2)
    second = run(setup.due.execute())
    assert (second.due, second.succeeded) == (1, 1)
    assert run(setup.due.execute()).due == 0


def test_concurrency_is_bounded(world: World, manager: User) -> None:
    probe = ConcurrencyProbe(world)
    setup = Setup(world, manager, probe, max_concurrency=2)
    for handle in ("a.vn", "b.vn", "c.vn", "d.vn"):
        setup.channel(handle)
    report = run(setup.due.execute())
    assert report.succeeded == 4
    assert probe.peak == 2
