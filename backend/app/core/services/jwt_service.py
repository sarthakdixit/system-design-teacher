from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.domain.errors import TokenExpired, TokenInvalid


class JWTClaims(BaseModel):
    model_config = ConfigDict(frozen=True)

    sub: str = Field(description="Subject — the user's microsoft_oid.")
    email: EmailStr
    name: str
    iat: int = Field(description="Issued-at, UNIX seconds.")
    exp: int = Field(description="Expiry, UNIX seconds.")


class JWTService:
    def __init__(
        self,
        *,
        secret: str,
        algorithm: str = "HS256",
        expiry_hours: int = 24,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expiry = timedelta(hours=expiry_hours)

    def issue(self, *, microsoft_oid: str, email: str, display_name: str) -> str:
        now = datetime.now(timezone.utc)
        claims = JWTClaims(
            sub=microsoft_oid,
            email=email,
            name=display_name,
            iat=int(now.timestamp()),
            exp=int((now + self._expiry).timestamp()),
        )
        return jwt.encode(claims.model_dump(), self._secret, algorithm=self._algorithm)

    def verify(self, token: str) -> JWTClaims:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpired("JWT has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalid(f"JWT is invalid: {exc}") from exc
        try:
            return JWTClaims.model_validate(payload)
        except Exception as exc:
            raise TokenInvalid(f"JWT payload does not match expected schema: {exc}") from exc