import pytest

from tests.unit.application.conftest import World, add_channel, run
from vinichannels.application.dto import UNSET
from vinichannels.application.errors import Conflict, NotFound, PermissionDenied
from vinichannels.application.use_cases.channels.crud import ListChannels
from vinichannels.application.use_cases.partners.crud import (
    ArchivePartner,
    CreatePartner,
    GetPartner,
    ListPartners,
    RestorePartner,
    UpdatePartner,
    UpdatePartnerCommand,
)
from vinichannels.domain.identity.entities import User


def test_create_partner_normalizes_and_blocks_duplicates(world: World, manager: User) -> None:
    create = CreatePartner(world.uow, world.clock)
    created = run(create.execute(manager, " Brand A ", tags=frozenset({"Food", "vn"})))
    assert created.name == "Brand A"
    assert created.tags == ("food", "vn")
    with pytest.raises(Conflict):
        run(create.execute(manager, "brand a"))


def test_create_partner_rejects_unknown_owner(world: World, manager: User) -> None:
    with pytest.raises(NotFound):
        create = CreatePartner(world.uow, world.clock)
        run(create.execute(manager, "Brand", owner_user_id="missing"))


def test_viewer_can_read_but_not_write(world: World, manager: User, viewer: User) -> None:
    created = run(CreatePartner(world.uow, world.clock).execute(manager, "Brand A"))
    assert run(GetPartner(world.uow).execute(viewer, created.id)).name == "Brand A"
    with pytest.raises(PermissionDenied):
        run(CreatePartner(world.uow, world.clock).execute(viewer, "Other"))


def test_update_partner_only_touches_given_fields(world: World, manager: User) -> None:
    create = CreatePartner(world.uow, world.clock)
    created = run(create.execute(manager, "Brand A", industry="Food", notes="n"))
    updated = run(
        UpdatePartner(world.uow, world.clock).execute(
            manager, UpdatePartnerCommand(created.id, industry=None, tags=frozenset({"Hot"}))
        )
    )
    assert updated.industry is None
    assert updated.notes == "n"
    assert updated.name == "Brand A"
    assert updated.tags == ("hot",)
    assert UpdatePartnerCommand("x").name is UNSET


def test_list_partners_filters_and_counts_channels(world: World, manager: User) -> None:
    create = CreatePartner(world.uow, world.clock)
    a = run(create.execute(manager, "Alpha", tags=frozenset({"food"})))
    run(create.execute(manager, "Beta", industry="Fashion"))
    add_channel(world, a.id, "alpha.vn")
    listing = ListPartners(world.uow)
    assert [p.name for p in run(listing.execute(manager))] == ["Alpha", "Beta"]
    assert [p.name for p in run(listing.execute(manager, tag="food"))] == ["Alpha"]
    assert [p.name for p in run(listing.execute(manager, search="fash"))] == ["Beta"]
    assert run(listing.execute(manager))[0].channel_count == 1


def test_archive_cascades_to_channels_and_restore_keeps_them_archived(
    world: World, manager: User
) -> None:
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha"))
    add_channel(world, partner.id, "alpha.vn")
    archived = run(ArchivePartner(world.uow, world.clock).execute(manager, partner.id))
    assert archived.archived_at == world.clock.now()
    assert run(ListPartners(world.uow).execute(manager)) == []
    assert run(ListChannels(world.uow).execute(manager)) == []
    assert len(run(ListChannels(world.uow).execute(manager, include_archived=True))) == 1
    restored = run(RestorePartner(world.uow, world.clock).execute(manager, partner.id))
    assert restored.archived_at is None
    assert run(ListChannels(world.uow).execute(manager)) == []
