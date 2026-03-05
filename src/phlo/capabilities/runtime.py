"""Runtime context protocol and helpers for capability execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class RuntimeRouting:
    """Canonical runtime routing data shared across capabilities."""

    environment: str | None = None
    ref: str | None = None
    partition_key: str | None = None
    run_id: str | None = None
    resources: dict[str, Any] = field(default_factory=dict)
    feature_flags: dict[str, str] = field(default_factory=dict)


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

    @property
    def routing(self) -> RuntimeRouting:
        """Return canonical runtime routing information."""
        ...

    def get_resource(self, name: str) -> Any:
        """Return a runtime resource by name.

        Args:
            name: Resource identifier.

        Returns:
            Any: Resource object for the provided name.
        """
        ...


def routing_from_context(context: RuntimeContext) -> RuntimeRouting:
    """Build canonical routing data from a runtime context.

    This helper keeps the initial migration path lightweight for existing
    contexts that expose only tags, resources, and the standard protocol
    fields.
    """
    direct_routing = getattr(context, "routing", None)
    if isinstance(direct_routing, RuntimeRouting):
        return direct_routing

    resources_value = getattr(context, "resources", {})
    resources = dict(resources_value) if isinstance(resources_value, Mapping) else {}

    tags_value = getattr(context, "tags", {})
    tags = (
        {str(key): str(value) for key, value in tags_value.items()}
        if isinstance(tags_value, Mapping)
        else {}
    )
    feature_flags = {
        key.removeprefix("feature/"): value
        for key, value in tags.items()
        if key.startswith("feature/")
    }
    environment = tags.get("environment") or tags.get("env")
    ref = tags.get("phlo/ref") or tags.get("ref") or tags.get("branch")

    return RuntimeRouting(
        environment=environment,
        ref=ref,
        partition_key=getattr(context, "partition_key", None),
        run_id=getattr(context, "run_id", None),
        resources=resources,
        feature_flags=feature_flags,
    )
