"""Runtime context protocol for capability execution."""

from __future__ import annotations

from typing import Any, Protocol


class RuntimeContext(Protocol):
    """Orchestrator-agnostic runtime context."""

    run_id: str | None
    partition_key: str | None
    tags: dict[str, str]

    @property
    def logger(self) -> Any:
        """Return the orchestrator-provided logger."""
        ...

    @property
    def resources(self) -> dict[str, Any]:
        """Return runtime resources keyed by resource name."""
        ...

    def get_resource(self, name: str) -> Any:
        """Return a runtime resource by name.

        Args:
            name: Resource identifier.

        Returns:
            Any: Resource object for the provided name.
        """
        ...
