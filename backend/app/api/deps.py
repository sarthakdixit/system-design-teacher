from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.container import Container
from app.core.domain.errors import AuthenticationFailed
from app.core.domain.user import User
from app.core.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await auth_service.get_user_from_jwt(credentials.credentials)
    except AuthenticationFailed as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc