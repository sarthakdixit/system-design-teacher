from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user
from app.api.schemas.attempts import (
    AttemptResponse,
    PaginatedAttemptsResponse,
    RecordSituationAttemptRequest,
)
from app.config.container import Container
from app.core.domain.attempt import Attempt, AttemptType
from app.core.domain.user import User
from app.core.services.attempt_service import AttemptService, PaginatedAttempts

router = APIRouter(prefix="/api/v1/attempts", tags=["attempts"])


def _attempt_to_response(attempt: Attempt) -> AttemptResponse:
    return AttemptResponse(
        id=attempt.id,
        user_id=attempt.user_id,
        question_id=attempt.question_id,
        type=attempt.type,
        user_notes=attempt.user_notes,
        created_at=attempt.created_at,
    )


def _paginated_to_response(paginated: PaginatedAttempts) -> PaginatedAttemptsResponse:
    return PaginatedAttemptsResponse(
        items=[_attempt_to_response(a) for a in paginated.items],
        total=paginated.total,
        limit=paginated.limit,
        skip=paginated.skip,
    )


@router.post(
    "/situation",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record that the user practiced a situation question.",
)
@inject
async def record_situation_attempt(
    payload: RecordSituationAttemptRequest,
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(Provide[Container.attempt_service]),
) -> AttemptResponse:
    attempt = await service.record_situation_attempt(
        user_id=current_user.id,
        question_id=payload.question_id,
        user_notes=payload.user_notes,
    )
    return _attempt_to_response(attempt)


@router.get(
    "",
    response_model=PaginatedAttemptsResponse,
    summary="List the current user's attempts (most recent first).",
)
@inject
async def list_user_attempts(
    attempt_type: AttemptType | None = Query(default=None, alias="type"),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: AttemptService = Depends(Provide[Container.attempt_service]),
) -> PaginatedAttemptsResponse:
    paginated = await service.list_user_attempts(
        user_id=current_user.id,
        attempt_type=attempt_type,
        limit=limit,
        skip=skip,
    )
    return _paginated_to_response(paginated)