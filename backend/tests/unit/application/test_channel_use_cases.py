import pytest

from tests.unit.application.conftest import World, add_channel, run
from vinichannels.application.dto import UNSET
from vinichannels.application.errors import PermissionDenied
from vinichannels.application.use_cases.channels.crud import (
    ArchiveChannel,
    GetChannel,
    RestoreChannel,
    SetChannelSchedule,
    UpdateChannel,
    UpdateChannelCommand,
)
from vinichannels.application.use_cases.partners.crud import ArchivePartner, CreatePartner
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.partners.errors import PartnerArchived


def _partner_id(world: World, manager: User, name: str = "Alpha") -> str:
    return run(CreatePartner(world.uow, world.clock).execute(manager, name)).id


def test_update_and_archive_restore_channel(world: World, manager: User) -> None:
    partner_id = _partner_id(world, manager)
    channel = add_channel(world, partner_id, "alpha.vn")
    updated = run(
        UpdateChannel(world.uow, world.clock).execute(
            manager,
            UpdateChannelCommand(channel.id, display_name="Alpha Official", is_active=False),
        )
    )
    assert updated.display_name == "Alpha Official" and updated.is_active is False
    assert UpdateChannelCommand("x").avatar_url is UNSET
    archived = run(ArchiveChannel(world.uow, world.clock).execute(manager, channel.id))
    assert archived.archived_at is not None
    restored = run(RestoreChannel(world.uow, world.clock).execute(manager, channel.id))
    assert restored.archived_at is None and restored.is_active is True


def test_restore_channel_requires_active_partner(world: World, manager: User) -> None:
    partner_id = _partner_id(world, manager)
    channel = add_channel(world, partner_id, "alpha.vn")
    run(ArchivePartner(world.uow, world.clock).execute(manager, partner_id))
    with pytest.raises(PartnerArchived):
        run(RestoreChannel(world.uow, world.clock).execute(manager, channel.id))


def test_schedule_requires_sync_write(world: World, manager: User) -> None:
    analyst = world.user(Role.ANALYST)
    partner_id = _partner_id(world, manager)
    channel = add_channel(world, partner_id, "alpha.vn")
    set_schedule = SetChannelSchedule(world.uow, world.clock)
    with pytest.raises(PermissionDenied):
        run(set_schedule.execute(analyst, channel.id, "0 8 * * *", "Asia/Ho_Chi_Minh"))
    updated = run(set_schedule.execute(manager, channel.id, "0 8 * * 1", "Asia/Bangkok"))
    assert (updated.sync_cron, updated.timezone) == ("0 8 * * 1", "Asia/Bangkok")
    cleared = run(set_schedule.execute(manager, channel.id, None, "Asia/Bangkok"))
    assert cleared.sync_cron is None
    assert run(GetChannel(world.uow).execute(analyst, channel.id)).sync_cron is None
