"""Capability resolver for runtime provider selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from phlo.capabilities.registry import CapabilityRegistry, get_capability_registry
from phlo.capabilities.support import CapabilitySupport
from phlo.logging import get_logger

if TYPE_CHECKING:
    from phlo.plugins.base.plugin import PluginMetadata

logger = get_logger(__name__)

_CAPABILITY_LISTERS = {
    "table_store": "list_table_stores",
    "catalog": "list_catalogs",
    "catalog_scanner": "list_catalog_scanners",
    "query_engine": "list_query_engines",
    "object_store": "list_object_stores",
    "quality_backend": "list_quality_backends",
    "maintenance_read_model": "list_maintenance_read_models",
    "metadata_catalog": "list_metadata_catalogs",
    "lineage_sink": "list_lineage_sinks",
    "governance_backend": "list_governance_backends",
    "authorization_policy_backend": "list_authorization_policy_backends",
    "authentication_provider": "list_authentication_providers",
    "publish_target": "list_publish_targets",
    "alert_sink": "list_alert_sinks",
    "api_backend": "list_api_backends",
    "secret_backend": "list_secret_backends",
    "schema_migrator": "list_schema_migrators",
    "observability_backend": "list_observability_backends",
}


@dataclass(frozen=True)
class ResolutionResult:
    """Resolved provider object and metadata."""

    capability_type: str
    name: str
    provider: Any
    metadata: dict[str, Any]
    support: CapabilitySupport


def list_capabilities(
    capability_type: str,
    *,
    registry: CapabilityRegistry | None = None,
) -> list[str]:
    """List registered capability names for a given capability type."""
    registry = registry or get_capability_registry()
    list_method = _CAPABILITY_LISTERS.get(capability_type)
    if not list_method:
        logger.debug("capability_list_unknown_type", capability_type=capability_type)
        return []
    specs = getattr(registry, list_method)()
    logger.debug(
        "capability_listed",
        capability_type=capability_type,
        capability_count=len(specs),
    )
    return [spec.name for spec in specs]


def resolve_capability(
    capability_type: str,
    name: str | None = None,
    *,
    registry: CapabilityRegistry | None = None,
) -> ResolutionResult | None:
    """Resolve a capability provider by type and optional name.

    If ``name`` is omitted and exactly one provider is installed, resolve it.
    Otherwise return ``None`` so callers can surface deterministic guidance.
    """
    registry = registry or get_capability_registry()
    list_method = _CAPABILITY_LISTERS.get(capability_type)
    if not list_method:
        logger.debug(
            "capability_resolution_unknown_type",
            capability_type=capability_type,
            requested_name=name,
        )
        return None

    specs = getattr(registry, list_method)()
    if name is not None:
        for spec in specs:
            if spec.name == name:
                logger.debug(
                    "capability_resolved",
                    capability_type=capability_type,
                    capability_name=spec.name,
                )
                return ResolutionResult(
                    capability_type=capability_type,
                    name=spec.name,
                    provider=spec.provider,
                    metadata=spec.metadata,
                    support=spec.support,
                )
        logger.debug(
            "capability_resolution_name_not_found",
            capability_type=capability_type,
            requested_name=name,
            available_names=[spec.name for spec in specs],
        )
        return None

    if len(specs) != 1:
        logger.debug(
            "capability_resolution_ambiguous",
            capability_type=capability_type,
            candidate_count=len(specs),
            candidate_names=[spec.name for spec in specs],
        )
        return None
    spec = specs[0]
    logger.debug(
        "capability_resolved_default",
        capability_type=capability_type,
        capability_name=spec.name,
    )
    return ResolutionResult(
        capability_type=capability_type,
        name=spec.name,
        provider=spec.provider,
        metadata=spec.metadata,
        support=spec.support,
    )


def missing_required_capabilities(
    plugin: PluginMetadata,
    *,
    registry: CapabilityRegistry | None = None,
) -> list[str]:
    """Return capability requirements that are currently unsatisfied."""
    registry = registry or get_capability_registry()
    missing: list[str] = []

    for capability in plugin.requires_capabilities:
        if ":" in capability:
            capability_type, expected_name = capability.split(":", 1)
            if resolve_capability(capability_type, expected_name, registry=registry) is None:
                missing.append(capability)
            continue

        if not list_capabilities(capability, registry=registry):
            missing.append(capability)

    if missing:
        logger.debug(
            "plugin_required_capabilities_missing",
            plugin_name=plugin.name,
            missing_capabilities=missing,
        )
    return missing
