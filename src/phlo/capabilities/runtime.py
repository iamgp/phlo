"""Runtime context protocol for capability execution."""

from __future__ import annotations

from typing import Any, Protocol


class RuntimeContext(Protocol):
    """Orchestrator-agnostic runtime context."""

    run_id: str | None
    partition_key: str | None
    tags: dict[str, str]

    @property
    def logger(self) -> Any: ...

    @property
    def resources(self) -> dict[str, Any]: ...

    def get_resource(self, name: str) -> Any: ...
