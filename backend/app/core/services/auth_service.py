from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.core.domain.user import NewUser, User
from app.core.ports.auth_provider import AuthProvider
from app.core.ports.database import Database
from app.core.ports.telemetry import Telemetry
from app.core.services.jwt_service import JWTClaims, JWTService


class LoginResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    user: User


class AuthService:
    def __init__(
        self,
        *,
        auth_provider: AuthProvider,
        database: Database,
        jwt_service: JWTService,
        telemetry: Telemetry,
    ) -> None:
        self._auth_provider = auth_provider
        self._database = database
        self._jwt_service = jwt_service
        self._telemetry = telemetry

    async def login_with_microsoft_token(self, microsoft_token: str) -> LoginResult:
        authenticated = await self._auth_provider.verify_token(microsoft_token)

        new_user = NewUser(
            microsoft_oid=authenticated.microsoft_oid,
            email=authenticated.email,
            display_name=authenticated.display_name,
        )
        user = await self._database.users.upsert_on_login(new_user)

        access_token = self._jwt_service.issue(
            microsoft_oid=user.microsoft_oid,
            email=user.email,
            display_name=user.display_name,
        )

        self._telemetry.log(
            "info",
            "user_login_succeeded",
            user_id=user.id,
            microsoft_oid=user.microsoft_oid,
        )
        self._telemetry.track_metric("user_login_count", 1.0)

        return LoginResult(access_token=access_token, user=user)

    async def get_user_from_jwt(self, token: str) -> User:
        claims: JWTClaims = self._jwt_service.verify(token)
        return await self._database.users.get_by_microsoft_oid(claims.sub)