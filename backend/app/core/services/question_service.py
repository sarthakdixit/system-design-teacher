from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.core.domain.question import Difficulty, Question
from app.core.ports.database import Database
from app.core.ports.telemetry import Telemetry
from app.core.services.rate_limit_service import (
    RateLimitedAction,
    RateLimitOutcome,
    RateLimitService,
)


class FetchSituationQuestionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: Question
    rate_limit: RateLimitOutcome


class QuestionService:
    def __init__(
        self,
        *,
        database: Database,
        rate_limit_service: RateLimitService,
        telemetry: Telemetry,
    ) -> None:
        self._database = database
        self._rate_limit_service = rate_limit_service
        self._telemetry = telemetry

    async def fetch_random_situation_question(
        self,
        *,
        microsoft_oid: str,
        category: str | None,
        difficulty: Difficulty | None,
    ) -> FetchSituationQuestionResult:
        outcome = await self._rate_limit_service.check_and_consume(
            action=RateLimitedAction.SITUATION_FETCH,
            microsoft_oid=microsoft_oid,
        )

        question = await self._database.questions.random_by_filter(
            type="situation",
            category=category,
            difficulty=difficulty,
        )

        self._telemetry.log(
            "info",
            "situation_question_fetched",
            question_id=question.id,
            category=question.category,
            difficulty=question.difficulty,
            user_remaining=outcome.user.remaining,
            global_remaining=outcome.global_.remaining,
        )
        self._telemetry.track_metric("situation_question_fetch_count", 1.0)

        return FetchSituationQuestionResult(question=question, rate_limit=outcome)

    async def fetch_random_design_question(
        self,
        *,
        category: str | None,
        difficulty: Difficulty | None,
    ) -> Question:
        question = await self._database.questions.random_by_filter(
            type="design_system",
            category=category,
            difficulty=difficulty,
        )

        self._telemetry.log(
            "info",
            "design_question_fetched",
            question_id=question.id,
            category=question.category,
            difficulty=question.difficulty,
        )
        self._telemetry.track_metric("design_question_fetch_count", 1.0)

        return question

    async def get_question_by_id(self, question_id: str) -> Question:
        return await self._database.questions.get_by_id(question_id)