from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ComponentType = Literal[
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

ALL_COMPONENT_TYPES: tuple[ComponentType, ...] = (
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
)

MAX_NODES = 200
MAX_EDGES = 500
MAX_LABEL_LENGTH = 80


class DiagramNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    type: ComponentType
    label: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)


class DiagramEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    source_id: str = Field(min_length=1, max_length=100)
    target_id: str = Field(min_length=1, max_length=100)


class Diagram(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    nodes: list[DiagramNode] = Field(min_length=1, max_length=MAX_NODES)
    edges: list[DiagramEdge] = Field(default_factory=list, max_length=MAX_EDGES)