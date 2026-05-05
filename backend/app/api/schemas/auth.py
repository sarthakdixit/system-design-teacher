from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MicrosoftCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    microsoft_token: str = Field(
        min_length=1,
        description="The Microsoft ID token returned by MSAL on the frontend.",
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    microsoft_oid: str
    email: EmailStr
    display_name: str
    created_at: datetime
    last_login_at: datetime


class LoginResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str = Field(description="The backend-issued JWT to send on subsequent requests.")
    token_type: str = Field(default="Bearer")
    expires_in_seconds: int = Field(description="Seconds until the access token expires.")
    user: UserResponse
