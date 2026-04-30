from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

QuestionType = Literal["situation", "design_system"]
Difficulty = Literal["junior", "mid", "senior"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Question(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Database identifier (Mongo ObjectId as string).")
    type: QuestionType
    title: str
    prompt: str = Field(description="Full prompt text shown to the user.")
    category: str = Field(description="Topic category, e.g. 'caching', 'scalability'.")
    difficulty: Difficulty
    reference_answer: str | None = Field(
        default=None,
        description="Pre-generated reference answer for situation questions. None means not yet generated.",
    )
    tags: list[str] = Field(default_factory=list)
    is_ai_generated: bool = Field(default=False)
    created_at: datetime


class NewQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: QuestionType
    title: str
    prompt: str
    category: str
    difficulty: Difficulty
    reference_answer: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_ai_generated: bool = False
    created_at: datetime = Field(default_factory=_utcnow)