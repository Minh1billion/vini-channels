from typing import Annotated, cast

from fastapi import Depends, Request

from vinichannels.adapters.inbound.http.wiring import HttpConfig, UseCases
from vinichannels.application.errors import AuthenticationFailed
from vinichannels.domain.identity.entities import User


def get_use_cases(request: Request) -> UseCases:
    return cast(UseCases, request.app.state.use_cases)


def get_config(request: Request) -> HttpConfig:
    return cast(HttpConfig, request.app.state.config)


UseCasesDep = Annotated[UseCases, Depends(get_use_cases)]
ConfigDep = Annotated[HttpConfig, Depends(get_config)]


async def current_user(request: Request, use_cases: UseCasesDep, config: ConfigDep) -> User:
    token = request.cookies.get(config.cookie_name)
    if not token:
        raise AuthenticationFailed("Bạn chưa đăng nhập")
    return await use_cases.authenticate.execute(token)


CurrentUser = Annotated[User, Depends(current_user)]
