from fastapi import APIRouter, Response, status

from vinichannels.adapters.inbound.http.dependencies import ConfigDep, CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    UserResponse,
)
from vinichannels.application.dto import UserDTO

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
async def login(
    body: LoginRequest, response: Response, use_cases: UseCasesDep, config: ConfigDep
) -> UserResponse:
    result = await use_cases.login.execute(body.email, body.password)
    response.set_cookie(
        config.cookie_name,
        result.token,
        max_age=config.session_ttl_seconds,
        httponly=True,
        secure=config.cookie_secure,
        samesite="lax",
        path="/",
    )
    return UserResponse.model_validate(result.user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, config: ConfigDep) -> None:
    response.delete_cookie(config.cookie_name, path="/")


@router.get("/me")
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(UserDTO.from_entity(user))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest, user: CurrentUser, use_cases: UseCasesDep
) -> None:
    await use_cases.change_own_password.execute(user, body.current_password, body.new_password)
