from datetime import date, timedelta

import pytest

from tests.unit.application.conftest import World, run
from vinichannels.application.errors import PermissionDenied
from vinichannels.application.use_cases.audit.query import ListAuditLog
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.application.use_cases.scoring.scoring import UpdateScoringWeights
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.shared.errors import ValidationError


def test_weights_change_is_recorded_and_filterable(world: World, admin: User) -> None:
    run(CreatePartner(world.uow, world.clock).execute(admin, "Alpha"))
    world.clock.current += timedelta(days=2)
    run(UpdateScoringWeights(world.uow, world.clock).execute(admin, 0.5, 0.2, 0.2, 0.1))
    listing = ListAuditLog(world.uow)

    entries = run(listing.execute(admin, action=AuditAction.SCORING_WEIGHTS.value))
    assert len(entries) == 1
    assert entries[0].actor_id == admin.id
    assert entries[0].detail["engagement"] == "0.4 → 0.5"

    start = world.clock.current.date()
    assert len(run(listing.execute(admin))) == 2
    assert len(run(listing.execute(admin, date_from=start))) == 1
    assert len(run(listing.execute(admin, date_to=start - timedelta(days=1)))) == 1
    assert run(listing.execute(admin, actor_id="someone-else")) == []


def test_only_audit_readers_can_list_and_filters_are_validated(world: World, admin: User) -> None:
    listing = ListAuditLog(world.uow)
    for role in (Role.MANAGER, Role.ANALYST, Role.VIEWER):
        with pytest.raises(PermissionDenied):
            run(listing.execute(world.user(role)))
    with pytest.raises(ValidationError):
        run(listing.execute(admin, action="nope"))
    with pytest.raises(ValidationError):
        run(listing.execute(admin, date_from=date(2026, 10, 2), date_to=date(2026, 10, 1)))
