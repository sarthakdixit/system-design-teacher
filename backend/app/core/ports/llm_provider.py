from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

LLMModel = Literal["gpt-4o", "gpt-4o-mini", "stub"]


class LLMMessage(BaseModel):

    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


class LLMUsage(BaseModel):

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class LLMResponse(BaseModel):

    model_config = ConfigDict(frozen=True)

    content: str
    model: LLMModel
    usage: LLMUsage
    finish_reason: Literal["stop", "length", "content_filter", "error"]


class LLMError(Exception):
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMValidationError(LLMError):
    pass


@runtime_checkable
class LLMProvider(Protocol):

    async def generate(
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        ...

    async def generate_structured[T: BaseModel](
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        response_schema: type[T],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> tuple[T, LLMUsage]:
        ...

    async def health_check(self) -> bool:
        ...