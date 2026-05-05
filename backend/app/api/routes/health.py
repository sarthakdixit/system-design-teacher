from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.config.container import Container
from app.config.settings import Settings, get_settings
from app.core.services.health_service import DeepHealthReport, HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Shallow liveness probe",
    response_description="Trivial 200 if the process is up.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health/deep",
    summary="Deep readiness probe — exercises every port",
    response_model=DeepHealthReport,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": DeepHealthReport,
            "description": "One or more components are unhealthy.",
        }
    },
)
@inject
async def health_deep(
    settings: Settings = Depends(get_settings),
    service: HealthService = Depends(Provide[Container.health_service]),
) -> JSONResponse:
    report = await service.check_deep(environment=settings.environment)
    http_status = (
        status.HTTP_200_OK if report.status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=http_status, content=report.model_dump())
