from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.domain.errors import (
    AuthenticationFailed,
    DomainError,
    RateLimitExceeded,
    UserNotFound,
)
from app.core.ports.database import NotFoundError


def _problem(status_code: int, detail: str, **extra: object) -> JSONResponse:
    body: dict[str, object] = {"detail": detail, **extra}
    return JSONResponse(status_code=status_code, content=body)


async def _handle_authentication_failed(
    _request: Request, exc: AuthenticationFailed
) -> JSONResponse:
    response = _problem(status.HTTP_401_UNAUTHORIZED, str(exc) or "Authentication failed")
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def _handle_user_not_found(_request: Request, exc: UserNotFound) -> JSONResponse:
    return _problem(status.HTTP_404_NOT_FOUND, str(exc) or "User not found")


async def _handle_db_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
    return _problem(status.HTTP_404_NOT_FOUND, str(exc) or "Resource not found")


async def _handle_rate_limit(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return _problem(
        status.HTTP_429_TOO_MANY_REQUESTS,
        str(exc),
        limit=exc.limit,
        reset_in_seconds=exc.reset_in_seconds,
    )


async def _handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    return _problem(status.HTTP_400_BAD_REQUEST, str(exc) or "Bad request")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthenticationFailed, _handle_authentication_failed)
    app.add_exception_handler(UserNotFound, _handle_user_not_found)
    app.add_exception_handler(NotFoundError, _handle_db_not_found)
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limit)
    app.add_exception_handler(DomainError, _handle_domain_error)
