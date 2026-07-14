"""Runtime context protocol and helpers for capability execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from phlo._attempt import attempt_from_tags
from phlo._correlation import resolve_project_identity
from phlo.capabilities.support import CapabilitySupport


@dataclass(frozen=True, slots=True)
class RuntimeRouting:
    """Canonical runtime routing data shared across capabilities."""

    environment: str | None = None
    ref: str | None = None
    partition_key: str | None = None
    run_id: str | None = None
    project_id: str | None = None
    project_error: str | None = None
    attempt: int | None = 1
    attempt_error: str | None = None
    resources: dict[str, Any] = field(default_factory=dict)
    feature_flags: dict[str, str] = field(default_factory=dict)
    capability_overrides: dict[str, str] = field(default_factory=dict)


def capability_overrides_from_tags(tags: Mapping[str, str]) -> dict[str, str]:
    """Extract capability overrides from canonical runtime tags."""
    overrides: dict[str, str] = {}
    for key, value in tags.items():
        if not value:
            continue
        if key.startswith("phlo/capability/"):
            capability_type = key.removeprefix("phlo/capability/")
        elif key.startswith("capability/"):
            capability_type = key.removeprefix("capability/")
        else:
            continue
        capability_type = capability_type.strip()
        if capability_type:
            overrides[capability_type] = value
    return overrides


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
    capability_overrides = capability_overrides_from_tags(tags)
    environment = tags.get("environment") or tags.get("env")
    ref = tags.get("phlo/ref") or tags.get("ref") or tags.get("branch")

    attempt, attempt_error = attempt_from_tags(tags)
    project = resolve_project_identity(tags)
    return RuntimeRouting(
        environment=environment,
        ref=ref,
        partition_key=getattr(context, "partition_key", None),
        run_id=getattr(context, "run_id", None),
        project_id=project.project_id,
        project_error=project.error,
        attempt=attempt,
        attempt_error=attempt_error,
        resources=resources,
        feature_flags=feature_flags,
        capability_overrides=capability_overrides,
    )


def resolve_runtime_ref(
    context: RuntimeContext | None,
    *,
    support: CapabilitySupport | None = None,
    default_ref: str | None = None,
) -> str | None:
    """Resolve the effective ref for a capability from runtime routing and support metadata.

    Args:
        context: Runtime context or ``None`` when no orchestrator context exists.
        support: Capability support metadata. When refs are unsupported, routing refs are ignored.
        default_ref: Fallback ref used when the capability supports refs but the runtime omitted one.

    Returns:
        Effective ref name for the capability, or ``None`` when refs are unsupported.
    """
    if support is not None and not support.supports_refs:
        return None
    if context is not None:
        routing = routing_from_context(context)
        if routing.ref:
            return routing.ref
    return default_ref
