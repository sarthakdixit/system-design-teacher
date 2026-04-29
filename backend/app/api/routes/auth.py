from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.api.schemas.auth import LoginResponse, MicrosoftCallbackRequest, UserResponse
from app.config.container import Container
from app.config.settings import Settings, get_settings
from app.core.domain.user import User
from app.core.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        microsoft_oid=user.microsoft_oid,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post(
    "/microsoft/callback",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange a Microsoft ID token for a backend JWT.",
)
@inject
async def microsoft_callback(
    payload: MicrosoftCallbackRequest,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    result = await auth_service.login_with_microsoft_token(payload.microsoft_token)
    return LoginResponse(
        access_token=result.access_token,
        expires_in_seconds=settings.jwt.expiry_hours * 3600,
        user=_user_to_response(result.user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user's profile.",
)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_to_response(current_user)