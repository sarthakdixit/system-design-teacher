from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthenticatedUser(BaseModel):

    model_config = ConfigDict(frozen=True)

    microsoft_oid: str

    email: EmailStr
    display_name: str


class AuthError(Exception):
    pass


@runtime_checkable
class AuthProvider(Protocol):

    async def verify_token(self, token: str) -> AuthenticatedUser:
        ...

    async def health_check(self) -> bool:
        ...