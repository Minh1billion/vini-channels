import pytest

from vinichannels.domain.identity.entities import ROLE_PERMISSIONS, Permission, Role, User
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import UserId


def make_user(role: Role, active: bool = True) -> User:
    return User(UserId("u1"), "Minh@Example.com", role, "hash", is_active=active)


def test_email_is_normalized_and_validated() -> None:
    assert make_user(Role.ADMIN).email == "minh@example.com"
    with pytest.raises(ValidationError):
        User(UserId("u1"), "not-an-email", Role.ADMIN, "hash")


def test_admin_has_every_permission() -> None:
    assert ROLE_PERMISSIONS[Role.ADMIN] == frozenset(Permission)


@pytest.mark.parametrize(
    ("role", "permission", "allowed"),
    [
        (Role.MANAGER, Permission.PARTNERS_WRITE, True),
        (Role.MANAGER, Permission.SYNC_WRITE, True),
        (Role.MANAGER, Permission.SCORING_WRITE, False),
        (Role.MANAGER, Permission.USERS_WRITE, False),
        (Role.ANALYST, Permission.PARTNERS_WRITE, False),
        (Role.ANALYST, Permission.SYNC_READ, True),
        (Role.ANALYST, Permission.SYNC_WRITE, False),
        (Role.ANALYST, Permission.SCORING_WRITE, True),
        (Role.VIEWER, Permission.ANALYTICS_READ, True),
        (Role.VIEWER, Permission.REPORTS_EXPORT, True),
        (Role.VIEWER, Permission.SYNC_READ, False),
        (Role.VIEWER, Permission.SCORING_READ, False),
        (Role.VIEWER, Permission.AUDIT_READ, False),
    ],
)
def test_permission_matrix(role: Role, permission: Permission, allowed: bool) -> None:
    assert make_user(role).can(permission) is allowed


def test_inactive_user_has_no_permissions() -> None:
    user = make_user(Role.ADMIN, active=False)
    assert not any(user.can(permission) for permission in Permission)


def test_only_admin_can_read_audit_and_manage_users_and_providers() -> None:
    for permission in (Permission.AUDIT_READ, Permission.USERS_WRITE, Permission.PROVIDERS_WRITE):
        holders = [role for role in Role if permission in ROLE_PERMISSIONS[role]]
        assert holders == [Role.ADMIN]
