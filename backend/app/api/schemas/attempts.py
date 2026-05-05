from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.design_feedback import DesignFeedbackResponse
from app.api.schemas.diagrams import DiagramDTO
from app.api.schemas.questions import RateLimitMeta

AttemptType = Literal["situation", "design_system"]


class RecordSituationAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    user_notes: str | None = Field(default=None, max_length=5000)


class SubmitDesignAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    diagram: DiagramDTO
    user_notes: str | None = Field(default=None, max_length=5000)


class AttemptResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    user_id: str
    question_id: str
    type: AttemptType
    user_notes: str | None
    created_at: datetime


class PaginatedAttemptsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[AttemptResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    skip: int = Field(ge=0)


class SubmitDesignAttemptResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    attempt: AttemptResponse
    feedback: DesignFeedbackResponse
    cache_hit: bool = Field(
        description="True if the feedback was served from cache (free), false if newly generated."
    )
    rate_limit: RateLimitMeta
