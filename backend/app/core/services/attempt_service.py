from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain.attempt import Attempt, AttemptType, NewAttempt
from app.core.domain.errors import UserNotFound
from app.core.ports.database import Database, NotFoundError
from app.core.ports.telemetry import Telemetry


class PaginatedAttempts(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[Attempt]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    skip: int = Field(ge=0)


_MAX_PAGE_SIZE = 100


class AttemptService:
    def __init__(
        self,
        *,
        database: Database,
        telemetry: Telemetry,
    ) -> None:
        self._database = database
        self._telemetry = telemetry

    async def record_situation_attempt(
        self,
        *,
        user_id: str,
        question_id: str,
        user_notes: str | None,
    ) -> Attempt:
        try:
            await self._database.questions.get_by_id(question_id)
        except NotFoundError as exc:
            raise UserNotFound(f"Question {question_id!r} does not exist") from exc

        new_attempt = NewAttempt(
            user_id=user_id,
            question_id=question_id,
            type="situation",
            user_notes=user_notes,
        )
        attempt = await self._database.attempts.insert(new_attempt)

        self._telemetry.log(
            "info",
            "attempt_recorded",
            attempt_id=attempt.id,
            user_id=user_id,
            question_id=question_id,
            attempt_type="situation",
        )
        self._telemetry.track_metric(
            "attempt_recorded_count",
            1.0,
            attempt_type="situation",
        )
        return attempt

    async def list_user_attempts(
        self,
        *,
        user_id: str,
        attempt_type: AttemptType | None,
        limit: int,
        skip: int,
    ) -> PaginatedAttempts:
        bounded_limit = max(1, min(limit, _MAX_PAGE_SIZE))
        bounded_skip = max(0, skip)

        items = await self._database.attempts.list_by_user(
            user_id=user_id,
            attempt_type=attempt_type,
            limit=bounded_limit,
            skip=bounded_skip,
        )
        total = await self._database.attempts.count_by_user(
            user_id=user_id,
            attempt_type=attempt_type,
        )
        return PaginatedAttempts(
            items=items,
            total=total,
            limit=bounded_limit,
            skip=bounded_skip,
        )
