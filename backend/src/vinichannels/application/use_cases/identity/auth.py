from datetime import datetime

from vinichannels.application.dto import LoginResult, UserDTO
from vinichannels.application.errors import AccountLocked, AuthenticationFailed
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.security import PasswordHasher, SessionTokens
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import record
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import UserId, new_id

MIN_PASSWORD_LENGTH = 8


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Mật khẩu cần ít nhất {MIN_PASSWORD_LENGTH} ký tự")


def _locked_error(user: User, now: datetime) -> AccountLocked:
    remaining = max(1, int((user.locked_until - now).total_seconds())) if user.locked_until else 1
    minutes = max(1, -(-remaining // 60))
    return AccountLocked(
        f"Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {minutes} phút",
        remaining,
    )


class Login:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        hasher: PasswordHasher,
        tokens: SessionTokens,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    async def execute(self, email: str, password: str) -> LoginResult:
        now = self._clock.now()
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email.strip().lower())
            if user is None or not user.is_active:
                raise AuthenticationFailed("Email hoặc mật khẩu không đúng")
            if user.is_locked(now):
                raise _locked_error(user, now)
            if not self._hasher.verify(password, user.password_hash):
                locked = user.register_failed_login(now)
                await uow.users.save(user)
                await uow.commit()
                if locked:
                    raise _locked_error(user, now)
                raise AuthenticationFailed("Email hoặc mật khẩu không đúng")
            if user.has_login_failures():
                user.clear_login_failures()
                await uow.users.save(user)
                await uow.commit()
        return LoginResult(user=UserDTO.from_entity(user), token=self._tokens.issue(user.id))


class ChangeOwnPassword:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher, clock: Clock
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._clock = clock

    async def execute(self, actor: User, current_password: str, new_password: str) -> None:
        now = self._clock.now()
        async with self._uow_factory() as uow:
            user = await uow.users.get(actor.id)
            if user is None or not user.is_active:
                raise AuthenticationFailed("Tài khoản không còn hoạt động")
            if user.is_locked(now):
                raise _locked_error(user, now)
            if not self._hasher.verify(current_password, user.password_hash):
                locked = user.register_failed_login(now)
                await uow.users.save(user)
                await uow.commit()
                if locked:
                    raise _locked_error(user, now)
                raise ValidationError("Mật khẩu hiện tại không đúng")
            validate_password(new_password)
            if new_password == current_password:
                raise ValidationError("Mật khẩu mới phải khác mật khẩu hiện tại")
            user.password_hash = self._hasher.hash(new_password)
            user.clear_login_failures()
            await uow.users.save(user)
            await record(
                uow,
                self._clock,
                user,
                AuditAction.USER_PASSWORD,
                "user",
                user.id,
                user.email,
                {"password": "changed", "by": "self"},
            )
            await uow.commit()


class Authenticate:
    def __init__(self, uow_factory: UnitOfWorkFactory, tokens: SessionTokens) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens

    async def execute(self, token: str) -> User:
        user_id = self._tokens.verify(token)
        if user_id is None:
            raise AuthenticationFailed("Phiên đăng nhập không hợp lệ hoặc đã hết hạn")
        async with self._uow_factory() as uow:
            user = await uow.users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationFailed("Tài khoản không còn hoạt động")
        return user


class EnsureAdmin:
    def __init__(self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher

    async def execute(self, email: str, password: str) -> UserDTO | None:
        validate_password(password)
        async with self._uow_factory() as uow:
            if await uow.users.count() > 0:
                return None
            user = User(
                id=UserId(new_id()),
                email=email,
                role=Role.ADMIN,
                password_hash=self._hasher.hash(password),
            )
            await uow.users.add(user)
            await uow.commit()
        return UserDTO.from_entity(user)
