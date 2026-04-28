from __future__ import annotations

import sys
from typing import Any

import structlog

from app.core.ports.telemetry import LogLevel

_SENSITIVE_KEY_FRAGMENTS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "jwt",
    "cookie",
)


def _redact(fields: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for k, v in fields.items():
        lk = k.lower()
        if any(frag in lk for frag in _SENSITIVE_KEY_FRAGMENTS):
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted


def _configure_structlog_once(level: str = "INFO") -> None:
    if structlog.is_configured():
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(_level_to_int(level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def _level_to_int(level: str) -> int:
    import logging
    return getattr(logging, level.upper(), logging.INFO)


class ConsoleTelemetry:

    def __init__(self, level: str = "INFO") -> None:
        _configure_structlog_once(level=level)
        self._logger = structlog.get_logger("app")

    def log(
        self,
        level: LogLevel,
        event: str,
        /,
        **fields: Any,
    ) -> None:
        method = getattr(self._logger, level)
        method(event, **_redact(fields))

    def track_metric(
        self,
        name: str,
        value: float,
        /,
        **tags: str,
    ) -> None:
        self._logger.info(
            "metric",
            metric=True,
            metric_name=name,
            metric_value=value,
            **_redact(dict(tags)),
        )

    def track_exception(
        self,
        exc: BaseException,
        /,
        **fields: Any,
    ) -> None:
        self._logger.error(
            "exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            exc_info=exc,
            **_redact(fields),
        )

    def bind(self, **context: Any) -> ConsoleTelemetry:
        new_instance = ConsoleTelemetry.__new__(ConsoleTelemetry)
        new_instance._logger = self._logger.bind(**_redact(context))
        return new_instance

    async def health_check(self) -> bool:
        return True