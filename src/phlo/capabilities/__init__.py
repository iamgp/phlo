"""Capability primitives and registry."""

from typing import TYPE_CHECKING

from phlo.capabilities.interfaces import SchemaExtractor, SchemaMigrator, TableStore
from phlo.capabilities.registry import (
    CapabilityRegistry,
    clear_capabilities,
    get_capability_registry,
    register_asset,
    register_catalog,
    register_check,
    register_data_migration_source,
    register_lineage_sink,
    register_metadata_catalog,
    register_publish_target,
    register_quality_backend,
    register_query_engine,
    register_resource,
    register_schema_migrator,
    register_table_store,
)
from phlo.capabilities.runtime import (
    RuntimeContext,
    RuntimeRouting,
    resolve_runtime_ref,
    routing_from_context,
)
from phlo.capabilities.specs import (
    AssetCheckSpec,
    AssetSpec,
    CatalogSpec,
    CheckResult,
    DataMigrationSourceSpec,
    FieldSpec,
    LineageSinkSpec,
    MaterializeResult,
    MetadataCatalogSpec,
    NormalizedSchema,
    PartitionSpec,
    PublishTargetSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    ResourceSpec,
    RunResult,
    RunSpec,
    SchemaChange,
    SchemaMigrationPlan,
    SchemaMigrationSpec,
    TableStoreSpec,
)
from phlo.capabilities.support import CapabilitySupport, coerce_capability_support

if TYPE_CHECKING:
    from phlo.capabilities.resolver import ResolutionResult

__all__ = [
    "AssetCheckSpec",
    "AssetSpec",
    "CatalogSpec",
    "CapabilitySupport",
    "CapabilityRegistry",
    "CheckResult",
    "DataMigrationSourceSpec",
    "FieldSpec",
    "LineageSinkSpec",
    "MaterializeResult",
    "MetadataCatalogSpec",
    "NormalizedSchema",
    "PartitionSpec",
    "PublishTargetSpec",
    "QualityBackendSpec",
    "QueryEngineSpec",
    "ResourceSpec",
    "RunResult",
    "RunSpec",
    "RuntimeContext",
    "RuntimeRouting",
    "SchemaChange",
    "SchemaExtractor",
    "SchemaMigrationPlan",
    "SchemaMigrationSpec",
    "SchemaMigrator",
    "TableStoreSpec",
    "TableStore",
    "coerce_capability_support",
    "clear_capabilities",
    "get_capability_registry",
    "list_capabilities",
    "missing_required_capabilities",
    "register_asset",
    "register_catalog",
    "register_check",
    "register_data_migration_source",
    "register_lineage_sink",
    "register_metadata_catalog",
    "register_publish_target",
    "register_quality_backend",
    "register_query_engine",
    "register_resource",
    "register_schema_migrator",
    "register_table_store",
    "ResolutionResult",
    "resolve_runtime_ref",
    "resolve_capability",
    "routing_from_context",
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
