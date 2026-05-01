from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain.diagram import (
    ALL_COMPONENT_TYPES,
    MAX_EDGES,
    MAX_LABEL_LENGTH,
    MAX_NODES,
)

ComponentTypeDTO = Literal[
    "user",
    "load_balancer",
    "api_gateway",
    "microservice",
    "auth_service",
    "cache",
    "database",
    "object_storage",
    "search_index",
    "cdn",
    "queue",
    "notification_service",
    "analytics",
    "rate_limiter",
]


class DiagramNodeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=100)
    type: ComponentTypeDTO
    label: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)


class DiagramEdgeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=100)
    source_id: str = Field(min_length=1, max_length=100)
    target_id: str = Field(min_length=1, max_length=100)


class DiagramDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: list[DiagramNodeDTO] = Field(min_length=1, max_length=MAX_NODES)
    edges: list[DiagramEdgeDTO] = Field(default_factory=list, max_length=MAX_EDGES)


COMPONENT_TYPES_TUPLE = ALL_COMPONENT_TYPES