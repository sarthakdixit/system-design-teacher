from __future__ import annotations

import logging
from typing import Any

import structlog
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import metrics, trace
from opentelemetry.metrics import Counter, Histogram

from app.core.ports.telemetry import LogLevel, Telemetry

_REDACTED_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "authorization",
        "jwt",
        "openai_api_key",
        "jwt_secret",
        "microsoft_token",
    }
)


def _redact(fields: dict[str, Any]) -> dict[str, Any]:
    return {k: ("***REDACTED***" if k.lower() in _REDACTED_KEYS else v) for k, v in fields.items()}


class AppInsightsTelemetry:
    def __init__(
        self,
        *,
        connection_string: str,
        service_name: str = "system-design-teacher",
    ) -> None:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="sdt",
            instrumentation_options={
                "azure_sdk": {"enabled": False},
                "django": {"enabled": False},
                "fastapi": {"enabled": True},
                "flask": {"enabled": False},
                "psycopg2": {"enabled": False},
                "requests": {"enabled": False},
                "urllib": {"enabled": False},
                "urllib3": {"enabled": False},
            },
        )

        self._service_name = service_name
        self._tracer = trace.get_tracer(service_name)
        self._meter = metrics.get_meter(service_name)
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._py_logger = logging.getLogger("sdt")
        self._struct_logger: structlog.stdlib.BoundLogger = structlog.get_logger("sdt")
        self._bound_context: dict[str, Any] = {}

    def log(self, level: LogLevel, event: str, /, **fields: Any) -> None:
        merged = {**self._bound_context, **fields}
        clean = _redact(merged)
        clean["event"] = event
        clean["service"] = self._service_name

        py_level = self._level_to_python(level)
        message = f"{event} {clean}"
        self._py_logger.log(py_level, message, extra=clean)

    def track_metric(self, name: str, value: float, /, **tags: str) -> None:
        clean_tags = {k: str(v) for k, v in tags.items()}

        if name.endswith("_ms") or name.endswith("_seconds") or name.endswith("_bytes"):
            histogram = self._histograms.get(name)
            if histogram is None:
                histogram = self._meter.create_histogram(
                    name=name,
                    description=f"Histogram for {name}",
                )
                self._histograms[name] = histogram
            histogram.record(value, attributes=clean_tags)
            return

        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(
                name=name,
                description=f"Counter for {name}",
            )
            self._counters[name] = counter
        counter.add(value, attributes=clean_tags)

    def track_exception(self, exc: BaseException, /, **fields: Any) -> None:
        merged = {**self._bound_context, **fields}
        clean = _redact(merged)
        clean["service"] = self._service_name
        clean["exception_type"] = type(exc).__name__

        self._py_logger.exception(
            f"exception_caught: {type(exc).__name__}",
            extra=clean,
        )

        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.record_exception(exc, attributes={k: str(v) for k, v in clean.items()})

    def bind(self, **context: Any) -> Telemetry:
        clone = AppInsightsTelemetry.__new__(AppInsightsTelemetry)
        clone._service_name = self._service_name
        clone._tracer = self._tracer
        clone._meter = self._meter
        clone._counters = self._counters
        clone._histograms = self._histograms
        clone._py_logger = self._py_logger
        clone._struct_logger = self._struct_logger
        clone._bound_context = {**self._bound_context, **context}
        return clone

    async def health_check(self) -> bool:
        try:
            return self._tracer is not None and self._meter is not None
        except Exception:
            return False

    @staticmethod
    def _level_to_python(level: LogLevel) -> int:
        return {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }.get(level, logging.INFO)
