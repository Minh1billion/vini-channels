from dataclasses import dataclass

from vinichannels.application.authorization import require
from vinichannels.application.dto import UNSET, Maybe, Unset, UserDTO
from vinichannels.application.errors import Conflict, NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.security import PasswordHasher
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import change, record
from vinichannels.application.use_cases.identity.auth import validate_password
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Permission, Role, User
from vinichannels.domain.shared.ids import UserId, new_id


class CreateUser:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher, clock: Clock
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._clock = clock

    async def execute(self, actor: User, email: str, password: str, role: Role) -> UserDTO:
        require(actor, Permission.USERS_WRITE)
        validate_password(password)
        async with self._uow_factory() as uow:
            user = User(
                id=UserId(new_id()),
                email=email,
                role=role,
                password_hash=self._hasher.hash(password),
            )
            if await uow.users.get_by_email(user.email) is not None:
                raise Conflict("Email đã được sử dụng")
            await uow.users.add(user)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.USER_CREATE,
                "user",
                user.id,
                user.email,
                {"role": user.role.value},
            )
            await uow.commit()
        return UserDTO.from_entity(user)


class ListUsers:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User) -> list[UserDTO]:
        require(actor, Permission.USERS_WRITE)
        async with self._uow_factory() as uow:
            users = await uow.users.list_all()
        return [UserDTO.from_entity(user) for user in users]


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: str
    role: Maybe[Role] = UNSET
    is_active: Maybe[bool] = UNSET
    password: Maybe[str] = UNSET


class UpdateUser:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher, clock: Clock
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._clock = clock

    async def execute(self, actor: User, command: UpdateUserCommand) -> UserDTO:
        require(actor, Permission.USERS_WRITE)
        async with self._uow_factory() as uow:
            user = await uow.users.get(UserId(command.user_id))
            if user is None:
                raise NotFound("Không tìm thấy người dùng")
            is_self = user.id == actor.id
            events: list[tuple[AuditAction, dict[str, str]]] = []
            if not isinstance(command.role, Unset):
                if is_self and command.role is not user.role:
                    raise Conflict("Không thể tự đổi vai trò của chính mình")
                if command.role is not user.role:
                    role_change = change(user.role.value, command.role.value)
                    events.append((AuditAction.USER_ROLE, {"role": role_change}))
                user.change_role(command.role)
            if not isinstance(command.is_active, Unset):
                if is_self and not command.is_active:
                    raise Conflict("Không thể tự vô hiệu hóa chính mình")
                if command.is_active != user.is_active:
                    status_change = change(user.is_active, command.is_active)
                    events.append((AuditAction.USER_STATUS, {"is_active": status_change}))
                user.is_active = command.is_active
                if command.is_active:
                    user.clear_login_failures()
            if not isinstance(command.password, Unset):
                validate_password(command.password)
                user.password_hash = self._hasher.hash(command.password)
                user.clear_login_failures()
                events.append((AuditAction.USER_PASSWORD, {"password": "changed"}))
            await uow.users.save(user)
            for action, detail in events:
                await record(uow, self._clock, actor, action, "user", user.id, user.email, detail)
            await uow.commit()
        return UserDTO.from_entity(user)
