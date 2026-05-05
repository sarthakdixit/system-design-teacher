from __future__ import annotations

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


class FeedbackItemResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    severity: Severity
    category: FeedbackCategory
    title: str
    description: str
    affected_components: list[str]
    suggested_change: str


class DesignFeedbackResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall_score: int = Field(ge=1, le=10)
    strengths: list[str]
    gaps: list[FeedbackItemResponse]
    missing_components: list[str]
    tradeoff_questions: list[str]
    estimated_level: EstimatedLevel
    llm_model: str
    llm_tokens_used: int = Field(ge=0)
