from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.schemas.rate_limits import AllRateLimitsResponse, RateLimitStatus
from app.config.container import Container
from app.core.domain.user import User
from app.core.services.rate_limit_service import (
    RateLimitedAction,
    RateLimitOutcome,
    RateLimitService,
)

router = APIRouter(prefix="/api/v1/rate-limits", tags=["rate-limits"])


def _outcome_to_status(outcome: RateLimitOutcome) -> RateLimitStatus:
    return RateLimitStatus(
        user_current=outcome.user.current_count,
        user_limit=outcome.user.limit,
        user_remaining=outcome.user.remaining,
        global_current=outcome.global_.current_count,
        global_limit=outcome.global_.limit,
        global_remaining=outcome.global_.remaining,
        reset_in_seconds=min(
            outcome.user.reset_in_seconds,
            outcome.global_.reset_in_seconds,
        ),
    )


@router.get(
    "",
    response_model=AllRateLimitsResponse,
    summary="Return the current user's rate-limit usage across all actions.",
)
@inject
async def get_all_rate_limits(
    current_user: User = Depends(get_current_user),
    service: RateLimitService = Depends(Provide[Container.rate_limit_service]),
) -> AllRateLimitsResponse:
    situation = await service.peek(
        action=RateLimitedAction.SITUATION_FETCH,
        microsoft_oid=current_user.microsoft_oid,
    )
    design = await service.peek(
        action=RateLimitedAction.DESIGN_SUBMISSION,
        microsoft_oid=current_user.microsoft_oid,
    )
    return AllRateLimitsResponse(
        situation_fetch=_outcome_to_status(situation),
        design_submission=_outcome_to_status(design),
    )