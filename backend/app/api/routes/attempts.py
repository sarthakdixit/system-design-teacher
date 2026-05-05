from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user
from app.api.schemas.attempts import (
    AttemptResponse,
    PaginatedAttemptsResponse,
    RecordSituationAttemptRequest,
    SubmitDesignAttemptRequest,
    SubmitDesignAttemptResponse,
)
from app.api.schemas.design_feedback import (
    DesignFeedbackResponse,
    FeedbackItemResponse,
)
from app.api.schemas.questions import RateLimitMeta
from app.config.container import Container
from app.core.domain.attempt import Attempt, AttemptType
from app.core.domain.design_feedback import DesignFeedback, FeedbackItem
from app.core.domain.diagram import Diagram, DiagramEdge, DiagramNode
from app.core.domain.user import User
from app.core.services.attempt_service import AttemptService, PaginatedAttempts
from app.core.services.design_feedback_service import (
    DesignFeedbackService,
    SubmitDesignResult,
)

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


def _feedback_item_to_response(item: FeedbackItem) -> FeedbackItemResponse:
    return FeedbackItemResponse(
        severity=item.severity,
        category=item.category,
        title=item.title,
        description=item.description,
        affected_components=list(item.affected_components),
        suggested_change=item.suggested_change,
    )


def _feedback_to_response(feedback: DesignFeedback) -> DesignFeedbackResponse:
    return DesignFeedbackResponse(
        overall_score=feedback.overall_score,
        strengths=list(feedback.strengths),
        gaps=[_feedback_item_to_response(g) for g in feedback.gaps],
        missing_components=list(feedback.missing_components),
        tradeoff_questions=list(feedback.tradeoff_questions),
        estimated_level=feedback.estimated_level,
        llm_model=feedback.llm_model,
        llm_tokens_used=feedback.llm_tokens_used,
    )


def _design_result_to_response(result: SubmitDesignResult) -> SubmitDesignAttemptResponse:
    return SubmitDesignAttemptResponse(
        attempt=_attempt_to_response(result.attempt),
        feedback=_feedback_to_response(result.feedback),
        cache_hit=result.cache_hit,
        rate_limit=RateLimitMeta(
            user_remaining=result.rate_limit.user.remaining,
            user_limit=result.rate_limit.user.limit,
            global_remaining=result.rate_limit.global_.remaining,
            global_limit=result.rate_limit.global_.limit,
            reset_in_seconds=min(
                result.rate_limit.user.reset_in_seconds,
                result.rate_limit.global_.reset_in_seconds,
            ),
        ),
    )


def _request_to_diagram(payload: SubmitDesignAttemptRequest) -> Diagram:
    return Diagram(
        nodes=[DiagramNode(id=n.id, type=n.type, label=n.label) for n in payload.diagram.nodes],
        edges=[
            DiagramEdge(id=e.id, source_id=e.source_id, target_id=e.target_id)
            for e in payload.diagram.edges
        ],
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


@router.post(
    "/design",
    response_model=SubmitDesignAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a design diagram for AI feedback.",
)
@inject
async def submit_design_attempt(
    payload: SubmitDesignAttemptRequest,
    current_user: User = Depends(get_current_user),
    service: DesignFeedbackService = Depends(Provide[Container.design_feedback_service]),
) -> SubmitDesignAttemptResponse:
    diagram = _request_to_diagram(payload)
    result = await service.submit_design(
        microsoft_oid=current_user.microsoft_oid,
        user_id=current_user.id,
        question_id=payload.question_id,
        diagram=diagram,
        user_notes=payload.user_notes,
    )
    return _design_result_to_response(result)


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
