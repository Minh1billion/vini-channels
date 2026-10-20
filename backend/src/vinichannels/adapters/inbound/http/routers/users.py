from fastapi import APIRouter, status

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.auth import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from vinichannels.adapters.inbound.http.schemas.common import given
from vinichannels.application.use_cases.identity.users import UpdateUserCommand

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(user: CurrentUser, use_cases: UseCasesDep) -> list[UserResponse]:
    items = await use_cases.list_users.execute(user)
    return [UserResponse.model_validate(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> UserResponse:
    created = await use_cases.create_user.execute(user, body.email, body.password, body.role)
    return UserResponse.model_validate(created)


@router.patch("/{user_id}")
async def update_user(
    user_id: str, body: UserUpdateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> UserResponse:
    command = UpdateUserCommand(
        user_id=user_id,
        role=given(body.role),
        is_active=given(body.is_active),
        password=given(body.password),
    )
    updated = await use_cases.update_user.execute(user, command)
    return UserResponse.model_validate(updated)
