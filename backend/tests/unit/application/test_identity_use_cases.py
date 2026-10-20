import pytest

from tests.unit.application.conftest import World, run
from vinichannels.application.dto import UserDTO
from vinichannels.application.errors import (
    AccountLocked,
    AuthenticationFailed,
    Conflict,
    PermissionDenied,
)
from vinichannels.application.use_cases.identity.auth import (
    Authenticate,
    ChangeOwnPassword,
    EnsureAdmin,
    Login,
)
from vinichannels.application.use_cases.identity.users import (
    CreateUser,
    ListUsers,
    UpdateUser,
    UpdateUserCommand,
)
from vinichannels.domain.identity.entities import LOCK_DURATION, MAX_FAILED_LOGINS, Role, User
from vinichannels.domain.shared.errors import ValidationError


def test_login_and_authenticate_round_trip(world: World) -> None:
    user = world.user(Role.ANALYST, "analyst@example.com")
    login = Login(world.uow, world.hasher, world.tokens, world.clock)
    result = run(login.execute(" Analyst@Example.com ", "password123"))
    assert result.user == UserDTO.from_entity(user)
    resolved = run(Authenticate(world.uow, world.tokens).execute(result.token))
    assert resolved.id == user.id


def test_login_rejects_wrong_password_and_inactive_user(world: World) -> None:
    user = world.user(Role.VIEWER, "v@example.com")
    login = Login(world.uow, world.hasher, world.tokens, world.clock)
    with pytest.raises(AuthenticationFailed):
        run(login.execute("v@example.com", "wrong-password"))
    user.is_active = False
    world.uow.state.users[user.id] = user
    with pytest.raises(AuthenticationFailed):
        run(login.execute("v@example.com", "password123"))


def test_authenticate_rejects_unknown_token(world: World) -> None:
    with pytest.raises(AuthenticationFailed):
        run(Authenticate(world.uow, world.tokens).execute("nope"))


def test_ensure_admin_only_creates_first_user(world: World) -> None:
    ensure = EnsureAdmin(world.uow, world.hasher)
    first = run(ensure.execute("boss@example.com", "password123"))
    second = run(ensure.execute("other@example.com", "password123"))
    assert first is not None and first.role is Role.ADMIN
    assert second is None
    with pytest.raises(ValidationError):
        run(EnsureAdmin(world.uow, world.hasher).execute("x@example.com", "short"))


def test_only_admin_manages_users(world: World, admin: User, manager: User) -> None:
    create = CreateUser(world.uow, world.hasher, world.clock)
    created = run(create.execute(admin, "new@example.com", "password123", Role.MANAGER))
    assert created.role is Role.MANAGER
    with pytest.raises(Conflict):
        run(create.execute(admin, "NEW@example.com", "password123", Role.VIEWER))
    with pytest.raises(PermissionDenied):
        run(create.execute(manager, "x@example.com", "password123", Role.VIEWER))
    with pytest.raises(PermissionDenied):
        run(ListUsers(world.uow).execute(manager))
    assert len(run(ListUsers(world.uow).execute(admin))) == 3


def test_update_user_blocks_self_demotion_and_changes_others(
    world: World, admin: User, viewer: User
) -> None:
    update = UpdateUser(world.uow, world.hasher, world.clock)
    with pytest.raises(Conflict):
        run(update.execute(admin, UpdateUserCommand(admin.id, role=Role.VIEWER)))
    with pytest.raises(Conflict):
        run(update.execute(admin, UpdateUserCommand(admin.id, is_active=False)))
    changed = run(
        update.execute(admin, UpdateUserCommand(viewer.id, role=Role.ANALYST, is_active=False))
    )
    assert changed.role is Role.ANALYST and changed.is_active is False


def test_change_own_password_requires_current_password(world: World, viewer: User) -> None:
    change = ChangeOwnPassword(world.uow, world.hasher, world.clock)
    with pytest.raises(ValidationError):
        run(change.execute(viewer, "wrong-password", "new-password-1"))
    run(change.execute(viewer, "password123", "new-password-1"))
    login = Login(world.uow, world.hasher, world.tokens, world.clock)
    with pytest.raises(AuthenticationFailed):
        run(login.execute(viewer.email, "password123"))
    assert run(login.execute(viewer.email, "new-password-1")).user.id == viewer.id
    assert world.uow.state.audit_entries[-1].detail["password"] == "changed"


def test_login_locks_after_too_many_failures_then_recovers(world: World, viewer: User) -> None:
    login = Login(world.uow, world.hasher, world.tokens, world.clock)
    for _ in range(MAX_FAILED_LOGINS - 1):
        with pytest.raises(AuthenticationFailed):
            run(login.execute(viewer.email, "wrong-password"))
    with pytest.raises(AccountLocked):
        run(login.execute(viewer.email, "wrong-password"))
    with pytest.raises(AccountLocked):
        run(login.execute(viewer.email, "password123"))
    world.clock.current += LOCK_DURATION
    assert run(login.execute(viewer.email, "password123")).user.id == viewer.id
    assert viewer.failed_login_attempts == 0 and viewer.locked_until is None
