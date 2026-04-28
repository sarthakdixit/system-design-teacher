from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.ports.llm_provider import (
    LLMMessage,
    LLMModel,
    LLMResponse,
    LLMUsage,
    LLMValidationError,
)


_CANNED_TEXT = (
    "[stub LLM response] This adapter does not call OpenAI. "
    "Configure a real OPENAI_API_KEY and switch to OpenAILLMProvider for real output."
)


def _fake_usage(prompt_chars: int) -> LLMUsage:
    prompt_tokens = max(1, prompt_chars // 4)
    completion_tokens = len(_CANNED_TEXT) // 4
    return LLMUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


class StubLLMProvider:

    async def generate(
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        prompt_chars = sum(len(m.content) for m in messages)
        return LLMResponse(
            content=_CANNED_TEXT,
            model=model,
            usage=_fake_usage(prompt_chars),
            finish_reason="stop",
        )

    async def generate_structured[T: BaseModel](
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        response_schema: type[T],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> tuple[T, LLMUsage]:
        try:
            instance: T = response_schema()  # type: ignore[call-arg]
        except (TypeError, ValidationError) as exc:
            raise LLMValidationError(
                f"StubLLMProvider cannot synthesize a {response_schema.__name__}"
                " because it has required fields. Switch to OpenAILLMProvider"
                " (set a real OPENAI_API_KEY) for structured generation."
            ) from exc

        prompt_chars = sum(len(m.content) for m in messages)
        return instance, _fake_usage(prompt_chars)

    async def health_check(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "StubLLMProvider(no-network, returns canned text)"

    def _unused(self) -> Any:
        return None