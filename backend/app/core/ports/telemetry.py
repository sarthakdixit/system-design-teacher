from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable

LogLevel = Literal["debug", "info", "warning", "error", "critical"]


@runtime_checkable
class Telemetry(Protocol):

    def log(
        self,
        level: LogLevel,
        event: str,
        /,
        **fields: Any,
    ) -> None:
        ...

    def track_metric(
        self,
        name: str,
        value: float,
        /,
        **tags: str,
    ) -> None:
        ...

    def track_exception(
        self,
        exc: BaseException,
        /,
        **fields: Any,
    ) -> None:
        ...

    def bind(self, **context: Any) -> Telemetry:
        ...

    async def health_check(self) -> bool:
        ...