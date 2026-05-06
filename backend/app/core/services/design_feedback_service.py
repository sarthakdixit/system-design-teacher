from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.core.domain.attempt import Attempt, NewAttempt
from app.core.domain.design_feedback import DesignFeedback, NewCachedFeedback
from app.core.domain.diagram import Diagram
from app.core.domain.errors import DomainError
from app.core.ports.database import Database, NotFoundError
from app.core.ports.llm_provider import (
    LLMMessage,
    LLMModel,
    LLMProvider,
    LLMValidationError,
)
from app.core.ports.telemetry import Telemetry
from app.core.services.diagram_hash_service import DiagramHashService
from app.core.services.rate_limit_service import (
    RateLimitedAction,
    RateLimitOutcome,
    RateLimitService,
)

_DEFAULT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "design_feedback.md"
_DEFAULT_MODEL: LLMModel = "gpt-4o"
_DEFAULT_TEMPERATURE = 0.3


class InvalidDiagramError(DomainError):
    pass


class FeedbackUnavailableError(DomainError):
    pass


class SubmitDesignResult(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    attempt: Attempt
    feedback: DesignFeedback
    cache_hit: bool
    rate_limit: RateLimitOutcome


class DesignFeedbackService:
    def __init__(
        self,
        *,
        database: Database,
        llm_provider: LLMProvider,
        rate_limit_service: RateLimitService,
        diagram_hash_service: DiagramHashService,
        telemetry: Telemetry,
        cache_ttl_days: int,
        prompt_path: Path | None = None,
        model: LLMModel = _DEFAULT_MODEL,
    ) -> None:
        self._database = database
        self._llm = llm_provider
        self._rate_limit_service = rate_limit_service
        self._hash_service = diagram_hash_service
        self._telemetry = telemetry
        self._cache_ttl = timedelta(days=cache_ttl_days)
        self._model = model
        self._system_prompt = self._load_prompt(prompt_path or _DEFAULT_PROMPT_PATH)

    async def submit_design(
        self,
        *,
        microsoft_oid: str,
        user_id: str,
        question_id: str,
        diagram: Diagram,
        user_notes: str | None,
    ) -> SubmitDesignResult:
        self._validate_diagram_referential_integrity(diagram)

        question = await self._database.questions.get_by_id(question_id)
        if question.type != "design_system":
            raise InvalidDiagramError(
                f"Question {question_id!r} is not a design_system question (type={question.type!r})"
            )

        rate_limit_outcome = await self._rate_limit_service.check_and_consume(
            action=RateLimitedAction.DESIGN_SUBMISSION,
            microsoft_oid=microsoft_oid,
        )

        cache_key = self._hash_service.hash(question_id=question_id, diagram=diagram)

        cached = await self._try_get_cached(cache_key)
        if cached is not None:
            feedback = cached
            cache_hit = True
            self._telemetry.log(
                "info",
                "design_feedback_cache_hit",
                cache_key=cache_key,
                question_id=question_id,
            )
            self._telemetry.track_metric("design_feedback_cache_hit_count", 1.0)
        else:
            feedback = await self._generate_feedback(
                question_prompt=question.prompt,
                diagram=diagram,
                user_notes=user_notes,
            )
            cache_hit = False
            await self._store_in_cache(cache_key=cache_key, feedback=feedback)
            self._telemetry.log(
                "info",
                "design_feedback_generated",
                cache_key=cache_key,
                question_id=question_id,
                tokens_used=feedback.llm_tokens_used,
                model=feedback.llm_model,
            )
            self._telemetry.track_metric("design_feedback_cache_miss_count", 1.0)
            self._telemetry.track_metric(
                "design_feedback_tokens_used",
                float(feedback.llm_tokens_used),
                model=feedback.llm_model,
            )

        new_attempt = NewAttempt(
            user_id=user_id,
            question_id=question_id,
            type="design_system",
            user_notes=user_notes,
        )
        attempt = await self._database.attempts.insert(new_attempt)

        return SubmitDesignResult(
            attempt=attempt,
            feedback=feedback,
            cache_hit=cache_hit,
            rate_limit=rate_limit_outcome,
        )

    def _load_prompt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _validate_diagram_referential_integrity(self, diagram: Diagram) -> None:
        node_ids = {node.id for node in diagram.nodes}
        if len(node_ids) != len(diagram.nodes):
            raise InvalidDiagramError("Diagram contains duplicate node ids")

        edge_ids = {edge.id for edge in diagram.edges}
        if len(edge_ids) != len(diagram.edges):
            raise InvalidDiagramError("Diagram contains duplicate edge ids")

        for edge in diagram.edges:
            if edge.source_id not in node_ids:
                raise InvalidDiagramError(
                    f"Edge {edge.id!r} references unknown source node {edge.source_id!r}"
                )
            if edge.target_id not in node_ids:
                raise InvalidDiagramError(
                    f"Edge {edge.id!r} references unknown target node {edge.target_id!r}"
                )

    async def _try_get_cached(self, cache_key: str) -> DesignFeedback | None:
        try:
            cached = await self._database.feedback_cache.get(cache_key)
        except NotFoundError:
            return None

        try:
            await self._database.feedback_cache.increment_hit_count(cache_key)
        except Exception as exc:
            self._telemetry.track_exception(exc, component="feedback_cache_increment")

        return cached.feedback

    async def _store_in_cache(self, *, cache_key: str, feedback: DesignFeedback) -> None:
        now = datetime.now(UTC)
        new_entry = NewCachedFeedback(
            key=cache_key,
            feedback=feedback,
            created_at=now,
            expires_at=now + self._cache_ttl,
        )
        try:
            await self._database.feedback_cache.insert(new_entry)
        except Exception as exc:
            self._telemetry.track_exception(exc, component="feedback_cache_insert")

    async def _generate_feedback(
        self,
        *,
        question_prompt: str,
        diagram: Diagram,
        user_notes: str | None,
    ) -> DesignFeedback:
        diagram_json = diagram.model_dump_json(indent=2)
        notes_text = user_notes if user_notes else "(none provided)"

        user_message = (
            f"Question: {question_prompt}\n\n"
            f"<user_diagram>\n{diagram_json}\n</user_diagram>\n\n"
            f"<user_notes>\n{notes_text}\n</user_notes>\n\n"
            "Produce a DesignFeedback JSON object. Reference the candidate's nodes by their `id` "
            "field in `affected_components`. Be specific to what they actually drew."
        )

        messages = [
            LLMMessage(role="system", content=self._system_prompt),
            LLMMessage(role="user", content=user_message),
        ]

        try:
            feedback, usage = await self._llm.generate_structured(
                model=self._model,
                messages=messages,
                response_schema=DesignFeedback,
                temperature=_DEFAULT_TEMPERATURE,
                max_tokens=4000,
            )
        except LLMValidationError as exc:
            self._telemetry.log(
                "warning",
                "design_feedback_llm_parse_failed_retrying",
                error=str(exc),
            )
            retry_messages = messages + [
                LLMMessage(
                    role="user",
                    content=(
                        f"Your previous response did not match the required schema: {exc}. "
                        "Return only valid JSON matching the DesignFeedback schema, with no extra "
                        "text before or after."
                    ),
                )
            ]
            try:
                feedback, usage = await self._llm.generate_structured(
                    model=self._model,
                    messages=retry_messages,
                    response_schema=DesignFeedback,
                    temperature=_DEFAULT_TEMPERATURE,
                    max_tokens=4000,
                )
            except LLMValidationError as retry_exc:
                self._telemetry.track_exception(retry_exc, component="design_feedback_retry")
                raise FeedbackUnavailableError(
                    "AI feedback service is currently unavailable. Please try again."
                ) from retry_exc

        return feedback.model_copy(
            update={
                "llm_model": self._model,
                "llm_tokens_used": usage.total_tokens,
            }
        )
