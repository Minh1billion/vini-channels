from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from vinichannels.application.errors import (
    AccountLocked,
    ApplicationError,
    AuthenticationFailed,
    ChannelUnverified,
    Conflict,
    NotFound,
    PermissionDenied,
)
from vinichannels.domain.shared.errors import DomainError, InvalidStateError, ValidationError

Handler = Callable[[Request, Exception], Awaitable[JSONResponse]]


def _body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details}


def _for_status(status: int) -> Handler:
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, (DomainError, ApplicationError)):
            return JSONResponse(status_code=status, content=_body(exc.code, exc.message))
        return JSONResponse(status_code=500, content=_body("internal_error", "Lỗi hệ thống"))

    return handle


async def _account_locked(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AccountLocked):
        return JSONResponse(status_code=500, content=_body("internal_error", "Lỗi hệ thống"))
    return JSONResponse(
        status_code=429,
        content=_body(exc.code, exc.message),
        headers={"Retry-After": str(exc.retry_after_sec)},
    )


async def _request_validation(request: Request, exc: Exception) -> JSONResponse:
    details = jsonable_encoder(exc.errors()) if isinstance(exc, RequestValidationError) else None
    return JSONResponse(
        status_code=422,
        content=_body("validation_error", "Dữ liệu gửi lên không hợp lệ", details),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ValidationError, _for_status(422))
    app.add_exception_handler(InvalidStateError, _for_status(409))
    app.add_exception_handler(DomainError, _for_status(409))
    app.add_exception_handler(NotFound, _for_status(404))
    app.add_exception_handler(Conflict, _for_status(409))
    app.add_exception_handler(ChannelUnverified, _for_status(422))
    app.add_exception_handler(PermissionDenied, _for_status(403))
    app.add_exception_handler(AuthenticationFailed, _for_status(401))
    app.add_exception_handler(AccountLocked, _account_locked)
    app.add_exception_handler(RequestValidationError, _request_validation)
