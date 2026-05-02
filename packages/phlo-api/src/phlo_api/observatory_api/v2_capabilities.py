"""Capability inventory helpers for Observatory v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from phlo_api.observatory_api.v2_models import (
    V2CapabilityInventory,
    V2CapabilityProvider,
    V2CapabilitySupport,
    V2ExternalLink,
    V2Health,
    V2RouteRequirement,
    V2UiContribution,
)
from phlo_api.observatory_api.v2_metadata import safe_metadata

CAPABILITY_LISTERS: dict[str, str] = {
    "query_engine": "list_query_engines",
    "table_store": "list_table_stores",
    "catalog": "list_catalogs",
    "catalog_scanner": "list_catalog_scanners",
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
    "observability_backend": "list_observability_backends",
    "regulated_surface": "list_regulated_surfaces",
}

ROUTE_REQUIREMENTS = [
    V2RouteRequirement(
        route_id="overview",
        label="Overview",
        path="/v2",
        reason="Core lakehouse attention surface.",
    ),
    V2RouteRequirement(
        route_id="data",
        label="Data",
        path="/v2/data",
        required_any=["query_engine", "table_store"],
        reason="Install a query engine or table store to browse data.",
    ),
    V2RouteRequirement(
        route_id="assets",
        label="Assets",
        path="/v2/assets",
        required_any=["query_engine", "table_store", "lineage_sink"],
        optional=["quality_backend", "maintenance_read_model"],
        reason="Install asset metadata or lineage providers to inspect impact.",
    ),
    V2RouteRequirement(
        route_id="issues",
        label="Issues",
        path="/v2/quality",
        required_any=["quality_backend"],
        reason="Install a quality provider to triage issues.",
    ),
    V2RouteRequirement(
        route_id="quality",
        label="Quality",
        path="/v2/quality",
        required_any=["quality_backend"],
        nav=False,
        reason="Install a quality provider to triage checks.",
    ),
    V2RouteRequirement(
        route_id="logs",
        label="Logs",
        path="/v2/logs",
        required_any=["observability_backend"],
        optional=["maintenance_read_model"],
        reason="Install an observability backend to inspect logs.",
    ),
    V2RouteRequirement(
        route_id="branches",
        label="Changes",
        path="/v2/branches",
        required_any=["catalog"],
        optional=["table_store"],
        reason="Install a catalog provider with refs to compare changes.",
    ),
    V2RouteRequirement(
        route_id="operations",
        label="Operations",
        path="/v2/operations",
        required_any=["maintenance_read_model"],
        reason="Install a maintenance read-model provider to inspect operations.",
    ),
    V2RouteRequirement(
        route_id="runs",
        label="Runs",
        path="/v2/runs",
        optional=["maintenance_read_model"],
        reason="Core provider-neutral run history surface.",
    ),
    V2RouteRequirement(
        route_id="storage",
        label="Storage",
        path="/v2/storage",
        required_any=["table_store", "object_store"],
        nav=False,
        reason="Install a table store or object store to inspect storage surfaces.",
    ),
    V2RouteRequirement(
        route_id="observability",
        label="Observability",
        path="/v2/observability",
        required_any=["observability_backend"],
        optional=["alert_sink"],
        nav=False,
        reason="Install an observability backend to inspect telemetry surfaces.",
    ),
    V2RouteRequirement(
        route_id="governance",
        label="Governance",
        path="/v2/governance",
        required_any=[
            "governance_backend",
            "authorization_policy_backend",
            "authentication_provider",
            "regulated_surface",
        ],
        nav=False,
        reason="Install a governance or policy provider to inspect regulated surfaces.",
    ),
    V2RouteRequirement(
        route_id="catalog",
        label="Catalog",
        path="/v2/catalog",
        required_any=["metadata_catalog", "catalog_scanner"],
        nav=False,
        reason="Install a metadata catalog or scanner to inspect catalog surfaces.",
    ),
    V2RouteRequirement(
        route_id="apis",
        label="APIs",
        path="/v2/apis",
        required_any=["api_backend"],
        nav=False,
        reason="Install an API backend to inspect published API surfaces.",
    ),
    V2RouteRequirement(
        route_id="bi",
        label="BI",
        path="/v2/bi",
        required_any=["publish_target"],
        optional=["query_engine"],
        nav=False,
        reason="Install a publish target to inspect BI surfaces.",
    ),
    V2RouteRequirement(
        route_id="extensions",
        label="Extensions",
        path="/v2/extensions",
        required_any=["observatory_extension"],
        nav=False,
        reason="Extension inventory is available in Settings.",
    ),
    V2RouteRequirement(
        route_id="services",
        label="Services",
        path="/v2/services",
        reason="Core runtime service inventory.",
    ),
    V2RouteRequirement(
        route_id="settings",
        label="Settings",
        path="/v2/settings",
        reason="Core Observatory settings.",
    ),
]


def build_capability_inventory(registry: Any | None) -> V2CapabilityInventory:
    """Build the full provider-neutral capability inventory."""
    providers: dict[str, list[V2CapabilityProvider]] = {}
    ui_contributions: list[V2UiContribution] = []
    if registry is not None:
        for capability_type, method_name in CAPABILITY_LISTERS.items():
            providers[capability_type] = _providers_for_type(registry, capability_type, method_name)
        ui_contributions = _ui_contributions(registry)
    return V2CapabilityInventory(
        providers=providers,
        requirements=ROUTE_REQUIREMENTS,
        ui_contributions=ui_contributions,
    )


def _providers_for_type(
    registry: Any,
    capability_type: str,
    method_name: str,
) -> list[V2CapabilityProvider]:
    method = getattr(registry, method_name, None)
    if not callable(method):
        return []
    try:
        specs = method()
    except Exception:
        return []
    return [_provider_from_spec(capability_type, spec) for spec in specs]


def _provider_from_spec(capability_type: str, spec: Any) -> V2CapabilityProvider:
    raw_metadata = getattr(spec, "metadata", {})
    metadata = safe_metadata(raw_metadata)
    name = str(getattr(spec, "name", capability_type))
    return V2CapabilityProvider(
        capability_type=capability_type,
        name=name,
        display_name=str(metadata.get("display_name") or metadata.get("service_type") or name),
        package=str(metadata.get("package")) if metadata.get("package") else None,
        metadata=metadata,
        support=_support_from_spec(getattr(spec, "support", None)),
        health=V2Health(state="unknown", message="registered"),
        native_links=_native_links(raw_metadata),
    )


def _support_from_spec(value: Any) -> V2CapabilitySupport:
    if value is None:
        return V2CapabilitySupport()
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        payload = {}
    return V2CapabilitySupport(**{key: bool(raw) for key, raw in payload.items()})


def _native_links(metadata: Any) -> list[V2ExternalLink]:
    # Provider-native links often contain internal hosts or credentials. Keep the
    # capability inventory provider-neutral until explicit public link policy exists.
    return []


def _ui_contributions(registry: Any) -> list[V2UiContribution]:
    method = getattr(registry, "list_ui_contributions", None)
    if not callable(method):
        return []
    try:
        specs = method()
    except Exception:
        return []
    if isinstance(specs, str):
        return []
    try:
        iterator = iter(specs)
    except TypeError:
        return []

    contributions: list[V2UiContribution] = []
    for spec in iterator:
        contribution = _ui_contribution_from_spec(spec)
        if contribution is not None:
            contributions.append(contribution)
    return contributions


def _ui_contribution_from_spec(spec: Any) -> V2UiContribution | None:
    try:
        return V2UiContribution(
            name=_required_string(spec, "name"),
            capability_type=_required_string(spec, "capability_type"),
            capability_name=_required_string(spec, "capability_name"),
            surfaces=_string_list(_spec_value(spec, "surfaces", [])),
            read_models=_string_mapping(_spec_value(spec, "read_models", {})),
            actions=_string_list(_spec_value(spec, "actions", [])),
            # Provider-native UI links can expose internal hosts or secrets.
            # Keep them out until Observatory has an explicit public-link policy.
            native_links=[],
            metadata=safe_metadata(_spec_value(spec, "metadata", {})),
        )
    except Exception:
        return None


def _spec_value(spec: Any, key: str, default: Any = None) -> Any:
    if isinstance(spec, Mapping):
        if key in spec:
            return spec[key]
        if default is not None:
            return default
        raise KeyError(key)
    return getattr(spec, key) if default is None else getattr(spec, key, default)


def _required_string(spec: Any, key: str) -> str:
    value = _spec_value(spec, key)
    if value is None:
        raise ValueError(f"Missing UI contribution field: {key}")
    text = str(value)
    if not text:
        raise ValueError(f"Empty UI contribution field: {key}")
    return text


def _string_list(value: Any) -> list[str]:
    if value is None or isinstance(value, str | Mapping):
        return []
    try:
        return [str(item) for item in value if item is not None]
    except TypeError:
        return []


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): str(raw_value)
        for key, raw_value in value.items()
        if key is not None and raw_value is not None
    }
