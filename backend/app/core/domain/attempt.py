from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AttemptType = Literal["situation", "design_system"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Attempt(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Database identifier (Mongo ObjectId as string).")
    user_id: str
    question_id: str
    type: AttemptType
    user_notes: str | None = Field(default=None, max_length=5000)
    created_at: datetime


class NewAttempt(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: str
    question_id: str
    type: AttemptType
    user_notes: str | None = Field(default=None, max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)