from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

QuestionType = Literal["situation", "design_system"]
Difficulty = Literal["junior", "mid", "senior"]


class QuestionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    type: QuestionType
    title: str
    prompt: str
    category: str
    difficulty: Difficulty
    tags: list[str]
    is_ai_generated: bool
    created_at: datetime


class SituationQuestionResponse(QuestionResponse):
    reference_answer: str | None = Field(
        default=None,
        description="The pre-generated reference answer. Frontend hides this behind a 'Reveal' UI.",
    )


class RateLimitMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_remaining: int = Field(ge=0)
    user_limit: int = Field(gt=0)
    global_remaining: int = Field(ge=0)
    global_limit: int = Field(gt=0)
    reset_in_seconds: int = Field(ge=0)


class FetchSituationQuestionResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: SituationQuestionResponse
    rate_limit: RateLimitMeta