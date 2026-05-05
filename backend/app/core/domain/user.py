from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Database identifier (Mongo ObjectId as string).")
    microsoft_oid: str = Field(
        description="Microsoft Entra tenant-unique object id. Stable across logins."
    )
    email: EmailStr
    display_name: str
    created_at: datetime
    last_login_at: datetime


class NewUser(BaseModel):
    model_config = ConfigDict(frozen=True)

    microsoft_oid: str
    email: EmailStr
    display_name: str
    created_at: datetime = Field(default_factory=_utcnow)
    last_login_at: datetime = Field(default_factory=_utcnow)
