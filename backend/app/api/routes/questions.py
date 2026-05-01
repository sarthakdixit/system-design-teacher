from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user
from app.api.schemas.questions import (
    DesignQuestionResponse,
    FetchSituationQuestionResponse,
    QuestionResponse,
    RateLimitMeta,
    SituationQuestionResponse,
)
from app.config.container import Container
from app.core.domain.question import Difficulty, Question
from app.core.domain.user import User
from app.core.services.question_service import (
    FetchSituationQuestionResult,
    QuestionService,
)

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


def _question_to_situation_response(question: Question) -> SituationQuestionResponse:
    return SituationQuestionResponse(
        id=question.id,
        type=question.type,
        title=question.title,
        prompt=question.prompt,
        category=question.category,
        difficulty=question.difficulty,
        tags=list(question.tags),
        is_ai_generated=question.is_ai_generated,
        created_at=question.created_at,
        reference_answer=question.reference_answer,
    )


def _question_to_design_response(question: Question) -> DesignQuestionResponse:
    return DesignQuestionResponse(
        id=question.id,
        type=question.type,
        title=question.title,
        prompt=question.prompt,
        category=question.category,
        difficulty=question.difficulty,
        tags=list(question.tags),
        is_ai_generated=question.is_ai_generated,
        created_at=question.created_at,
    )


def _result_to_fetch_response(result: FetchSituationQuestionResult) -> FetchSituationQuestionResponse:
    return FetchSituationQuestionResponse(
        question=_question_to_situation_response(result.question),
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


@router.get(
    "/situation",
    response_model=FetchSituationQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch a random situation-based question matching optional filters.",
)
@inject
async def get_random_situation_question(
    category: str | None = Query(default=None),
    difficulty: Difficulty | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(Provide[Container.question_service]),
) -> FetchSituationQuestionResponse:
    result = await service.fetch_random_situation_question(
        microsoft_oid=current_user.microsoft_oid,
        category=category,
        difficulty=difficulty,
    )
    return _result_to_fetch_response(result)


@router.get(
    "/situation/{question_id}",
    response_model=SituationQuestionResponse,
    summary="Fetch a specific situation question by id.",
)
@inject
async def get_situation_question_by_id(
    question_id: str,
    _current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(Provide[Container.question_service]),
) -> SituationQuestionResponse:
    question = await service.get_question_by_id(question_id)
    return _question_to_situation_response(question)


@router.get(
    "/design",
    response_model=DesignQuestionResponse,
    summary="Fetch a random design-system question matching optional filters.",
)
@inject
async def get_random_design_question(
    category: str | None = Query(default=None),
    difficulty: Difficulty | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(Provide[Container.question_service]),
) -> DesignQuestionResponse:
    question = await service.fetch_random_design_question(
        category=category,
        difficulty=difficulty,
    )
    return _question_to_design_response(question)


@router.get(
    "/design/{question_id}",
    response_model=DesignQuestionResponse,
    summary="Fetch a specific design question by id.",
)
@inject
async def get_design_question_by_id(
    question_id: str,
    _current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(Provide[Container.question_service]),
) -> DesignQuestionResponse:
    question = await service.get_question_by_id(question_id)
    return _question_to_design_response(question)