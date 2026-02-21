"""Capability primitives and registry."""

from typing import TYPE_CHECKING

from phlo.capabilities.interfaces import TableStore
from phlo.capabilities.registry import (
    CapabilityRegistry,
    clear_capabilities,
    get_capability_registry,
    register_asset,
    register_catalog,
    register_check,
    register_lineage_sink,
    register_metadata_catalog,
    register_quality_backend,
    register_query_engine,
    register_resource,
    register_table_store,
)
from phlo.capabilities.runtime import RuntimeContext
from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CatalogSpec,
    CheckResult,
    LineageSinkSpec,
    MaterializeResult,
    MetadataCatalogSpec,
    PartitionSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    ResourceSpec,
    RunResult,
    RunSpec,
    TableStoreSpec,
)

if TYPE_CHECKING:
    from phlo.capabilities.resolver import ResolutionResult

__all__ = [
    "AssetCheckSpec",
    "AssetSpec",
    "CatalogSpec",
    "CapabilityRegistry",
    "CheckResult",
    "LineageSinkSpec",
    "MaterializeResult",
    "MetadataCatalogSpec",
    "PartitionSpec",
    "QualityBackendSpec",
    "QueryEngineSpec",
    "ResourceSpec",
    "RunResult",
    "RunSpec",
    "RuntimeContext",
    "TableStoreSpec",
    "TableStore",
    "clear_capabilities",
    "get_capability_registry",
    "list_capabilities",
    "missing_required_capabilities",
    "register_asset",
    "register_catalog",
    "register_check",
    "register_lineage_sink",
    "register_metadata_catalog",
    "register_quality_backend",
    "register_query_engine",
    "register_resource",
    "register_table_store",
    "ResolutionResult",
    "resolve_capability",
]


def __getattr__(name: str):
    """Lazily expose resolver symbols to avoid circular imports."""
    if name in {
        "ResolutionResult",
        "list_capabilities",
        "missing_required_capabilities",
        "resolve_capability",
    }:
        from phlo.capabilities import resolver

        return getattr(resolver, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
