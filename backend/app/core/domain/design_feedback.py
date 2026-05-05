from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["critical", "important", "suggestion"]
FeedbackCategory = Literal[
    "scalability",
    "reliability",
    "security",
    "cost",
    "data",
    "consistency",
    "observability",
    "other",
]
EstimatedLevel = Literal["junior", "mid", "senior"]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class FeedbackItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    severity: Severity
    category: FeedbackCategory
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    affected_components: list[str] = Field(default_factory=list, max_length=50)
    suggested_change: str = Field(min_length=1, max_length=1000)


class DesignFeedback(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    overall_score: int = Field(ge=1, le=10)
    strengths: list[str] = Field(default_factory=list, max_length=10)
    gaps: list[FeedbackItem] = Field(default_factory=list, max_length=20)
    missing_components: list[str] = Field(default_factory=list, max_length=20)
    tradeoff_questions: list[str] = Field(default_factory=list, max_length=10)
    estimated_level: EstimatedLevel
    llm_model: str = Field(min_length=1, max_length=100)
    llm_tokens_used: int = Field(ge=0)


class CachedFeedback(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    feedback: DesignFeedback
    hit_count: int = Field(ge=0)
    created_at: datetime
    expires_at: datetime


class NewCachedFeedback(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    feedback: DesignFeedback
    expires_at: datetime
    hit_count: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
