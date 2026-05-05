from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.ports.llm_provider import (
    LLMError,
    LLMMessage,
    LLMModel,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
    LLMUsage,
    LLMValidationError,
)

_OPENAI_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_TIMEOUT_SECONDS = 60.0


class OpenAILLMProvider:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _OPENAI_BASE_URL,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    async def generate(
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        body = self._build_request_body(
            model, messages, temperature, max_tokens, json_response=False
        )
        data = await self._post_chat_completion(body)
        return self._parse_response(data, model)

    async def generate_structured[T: BaseModel](
        self,
        *,
        model: LLMModel,
        messages: list[LLMMessage],
        response_schema: type[T],
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> tuple[T, LLMUsage]:
        body = self._build_request_body(
            model, messages, temperature, max_tokens, json_response=True
        )
        data = await self._post_chat_completion(body)
        response = self._parse_response(data, model)

        try:
            payload = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise LLMValidationError(f"Model did not return valid JSON: {exc}") from exc

        try:
            instance = response_schema.model_validate(payload)
        except ValidationError as exc:
            raise LLMValidationError(
                f"Model JSON did not validate against {response_schema.__name__}: {exc}"
            ) from exc

        return instance, response.usage

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(
                    f"{self._base_url}/models",
                    headers=self._auth_headers(),
                )
            return response.status_code == 200
        except Exception:
            return False

    def _build_request_body(
        self,
        model: LLMModel,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        json_response: bool,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if json_response:
            body["response_format"] = {"type": "json_object"}
        return body

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _post_chat_completion(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._auth_headers(),
                    json=body,
                )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"OpenAI request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        if response.status_code == 429:
            raise LLMRateLimitError(f"OpenAI rate limit hit: {response.text}")
        if response.status_code >= 400:
            raise LLMError(f"OpenAI returned {response.status_code}: {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise LLMError(f"OpenAI returned non-JSON response: {exc}") from exc

    def _parse_response(self, data: dict[str, Any], model: LLMModel) -> LLMResponse:
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason_raw = choice.get("finish_reason", "stop")
            usage_data = data["usage"]
            usage = LLMUsage(
                prompt_tokens=usage_data["prompt_tokens"],
                completion_tokens=usage_data["completion_tokens"],
                total_tokens=usage_data["total_tokens"],
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected OpenAI response shape: {exc}") from exc

        finish_reason = (
            finish_reason_raw
            if finish_reason_raw in {"stop", "length", "content_filter"}
            else "error"
        )

        return LLMResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
        )
