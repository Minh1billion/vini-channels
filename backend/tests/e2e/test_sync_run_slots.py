import asyncio
from datetime import UTC, datetime

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("aiosqlite")

from vinichannels.adapters.outbound.persistence.database import (
    create_engine,
    create_session_factory,
    migrate_to_head,
)
from vinichannels.adapters.outbound.persistence.repositories import (
    SqlChannelRepository,
    SqlPartnerRepository,
    SqlSyncRunRepository,
)
from vinichannels.application.errors import DuplicateSyncRun
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import ChannelId, PartnerId, SyncRunId, new_id
from vinichannels.domain.syncing.entities import SyncRun, SyncTrigger


def _run(
    channel_id: ChannelId, slot: datetime, trigger: SyncTrigger = SyncTrigger.SCHEDULED
) -> SyncRun:
    return SyncRun(
        id=SyncRunId(new_id()),
        channel_id=channel_id,
        scheduled_for=slot,
        trigger=trigger,
        started_at=slot,
    )


def test_latest_slots_and_duplicate_slot_in_sql() -> None:
    first = datetime(2026, 10, 19, 1, 0, tzinfo=UTC)
    second = datetime(2026, 10, 20, 1, 0, tzinfo=UTC)

    async def scenario() -> tuple[dict[str, datetime], bool, bool]:
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        await migrate_to_head(engine)
        factory = create_session_factory(engine)
        async with factory() as session:
            partner = Partner(PartnerId(new_id()), "Alpha")
            await SqlPartnerRepository(session).add(partner)
            channel = Channel(ChannelId(new_id()), partner.id, Handle("alpha.vn"), "")
            await SqlChannelRepository(session).add(channel)
            runs = SqlSyncRunRepository(session)
            await runs.add(_run(channel.id, first))
            await runs.add(_run(channel.id, second))
            await session.commit()
        async with factory() as session:
            slots = await SqlSyncRunRepository(session).latest_slots()
        async with factory() as session:
            duplicate = False
            try:
                await SqlSyncRunRepository(session).add(_run(channel.id, second))
            except DuplicateSyncRun:
                duplicate = True
        async with factory() as session:
            manual_same_slot = True
            try:
                await SqlSyncRunRepository(session).add(
                    _run(channel.id, second, SyncTrigger.MANUAL)
                )
                await session.commit()
            except DuplicateSyncRun:
                manual_same_slot = False
        await engine.dispose()
        return dict(slots), duplicate, manual_same_slot

    slots, duplicate, manual_same_slot = asyncio.run(scenario())
    assert list(slots.values()) == [second]
    assert slots[next(iter(slots))].tzinfo is not None
    assert duplicate is True
    assert manual_same_slot is True
