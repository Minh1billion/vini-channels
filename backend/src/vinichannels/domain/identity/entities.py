import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import UserId

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_FAILED_LOGINS = 5
LOCK_DURATION = timedelta(minutes=15)


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(StrEnum):
    USERS_WRITE = "users:write"
    PROVIDERS_WRITE = "providers:write"
    PARTNERS_READ = "partners:read"
    PARTNERS_WRITE = "partners:write"
    SYNC_READ = "sync:read"
    SYNC_WRITE = "sync:write"
    ANALYTICS_READ = "analytics:read"
    SCORING_READ = "scoring:read"
    SCORING_WRITE = "scoring:write"
    REPORTS_EXPORT = "reports:export"
    AUDIT_READ = "audit:read"


_COMMON = {
    Permission.PARTNERS_READ,
    Permission.ANALYTICS_READ,
    Permission.REPORTS_EXPORT,
}

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MANAGER: frozenset(
        _COMMON
        | {
            Permission.PARTNERS_WRITE,
            Permission.SYNC_READ,
            Permission.SYNC_WRITE,
            Permission.SCORING_READ,
        }
    ),
    Role.ANALYST: frozenset(
        _COMMON | {Permission.SYNC_READ, Permission.SCORING_READ, Permission.SCORING_WRITE}
    ),
    Role.VIEWER: frozenset(_COMMON),
}


@dataclass(slots=True)
class User:
    id: UserId
    email: str
    role: Role
    password_hash: str
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: datetime | None = None

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(self.email):
            raise ValidationError("Email không hợp lệ")

    def can(self, permission: Permission) -> bool:
        return self.is_active and permission in ROLE_PERMISSIONS[self.role]

    def change_role(self, role: Role) -> None:
        self.role = role

    def deactivate(self) -> None:
        self.is_active = False

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and now < self.locked_until

    def register_failed_login(self, now: datetime) -> bool:
        if self.locked_until is not None and now >= self.locked_until:
            self.clear_login_failures()
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= MAX_FAILED_LOGINS:
            self.locked_until = now + LOCK_DURATION
            self.failed_login_attempts = 0
            return True
        return False

    def clear_login_failures(self) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None

    def has_login_failures(self) -> bool:
        return self.failed_login_attempts > 0 or self.locked_until is not None
