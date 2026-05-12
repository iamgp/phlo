"""Capability primitives and registry for Phlo.

This module provides the capability system that enables runtime feature discovery
and dependency injection. Capabilities abstract concrete implementations of
features like query engines, table stores, and authentication providers.

The capability system allows Phlo to:
    - Register and discover implementations at runtime
    - Resolve capabilities based on configuration and availability
    - Provide a unified interface for diverse backends
    - Support plugin-based extensibility

Key Concepts:
    - **Capability**: An abstract feature (e.g., "query_engine")
    - **Provider**: A concrete implementation (e.g., TrinoQueryEngine)
    - **Specification**: Configuration for a capability instance
    - **Registry**: Thread-safe storage for capability specifications
    - **Resolution**: Selecting the best available provider

Capability Types:
    - ``query_engine``: SQL query execution (Trino, DuckDB, etc.)
    - ``table_store``: Table storage (Iceberg, Delta, etc.)
    - ``catalog``: Metadata catalog (Nessie, OpenMetadata, etc.)
    - ``object_store``: Object storage (MinIO, S3, etc.)
    - ``authentication``: User authentication providers
    - ``authorization``: Policy-based access control
    - ``observability``: Metrics and monitoring backends
    - ``alert_sink``: Alert notification destinations
    - ``quality_backend``: Data quality validation
    - ``schema_migrator``: Schema evolution management
    - ``maintenance_read_model``: Maintenance status tracking

Main Components:
    - :class:`CapabilityRegistry`: Thread-safe capability storage
    - :func:`get_capability_registry`: Access the global registry
    - :func:`resolve_capability`: Resolve a capability to a provider
    - :func:`register_*`: Functions to register capability implementations
    - :class:`CapabilitySupport`: Declare operational guarantees
    - :class:`RuntimeContext`: Context for capability resolution

Example:
    ```python
    from phlo.capabilities import (
        get_capability_registry,
        resolve_capability,
        register_query_engine,
        QueryEngineSpec,
    )
    from phlo.capabilities.interfaces import QueryEngine

    # Register a query engine
    registry = get_capability_registry()
    register_query_engine(
        "trino",
        QueryEngineSpec(
            provider=MyTrinoEngine(),
            metadata={"default_catalog": "iceberg"}
        )
    )

    # Resolve the best available query engine
    result = resolve_capability("query_engine")
    if result:
        engine: QueryEngine = result.provider
        rows = engine.execute("SELECT * FROM iceberg.my_table")
    ```

See Also:
    - :mod:`phlo.plugins.base`: Plugin base classes using capabilities
    - :mod:`phlo.capabilities.registry`: Capability registration
    - :mod:`phlo.capabilities.resolver`: Capability resolution
    - :mod:`phlo.capabilities.specs`: Capability specifications
    - :mod:`phlo.capabilities.interfaces`: Capability interfaces

Note:
    This module uses lazy loading for resolver functions to prevent
    circular imports during plugin discovery.
"""

from typing import TYPE_CHECKING

from phlo.capabilities.interfaces import (
    AlertSink,
    ApiBackend,
    AuthenticatedSession,
    AuthenticationProvider,
    AuthorizationDecision,
    AuthorizationPolicyBackend,
    AuthPrincipal,
    AuthResult,
    BrowserLoginStart,
    CatalogScanner,
    DecisionContext,
    LogoutResult,
    MaintenanceReadModel,
    ObservabilityBackend,
    Principal,
    QueryEngine,
    RequestContext,
    ResourceRef,
    SchemaExtractor,
    SchemaMigrator,
    TableStore,
    TraceSpan,
    TraceSpanFilter,
)
from phlo.capabilities.maintenance import (
    DefaultMaintenanceReadModel,
    MaintenanceOperationStatus,
    MaintenanceStatusSnapshot,
    load_maintenance_status,
    render_maintenance_prometheus,
)
from phlo.capabilities.observability import (
    DefaultObservabilityBackend,
    register_default_capability_providers,
)
from phlo.capabilities.registry import (
    CapabilityRegistry,
    clear_capabilities,
    get_capability_registry,
    list_regulated_surfaces,
    register_alert_sink,
    register_api_backend,
    register_asset,
    register_authentication_provider,
    register_authorization_policy_backend,
    register_catalog,
    register_catalog_scanner,
    register_check,
    register_data_migration_source,
    register_governance_backend,
    register_lineage_sink,
    register_maintenance_read_model,
    register_metadata_catalog,
    register_object_store,
    register_observability_backend,
    register_publish_target,
    register_quality_backend,
    register_query_engine,
    register_regulated_surface,
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
    AlertSinkSpec,
    ApiBackendSpec,
    AssetCheckSpec,
    AssetSpec,
    AuthenticationProviderSpec,
    AuthorizationPolicyBackendSpec,
    CatalogScannerSpec,
    CatalogSpec,
    CheckResult,
    DataMigrationSourceSpec,
    FieldSpec,
    GovernanceBackendSpec,
    LineageSinkSpec,
    MaintenanceReadModelSpec,
    MaterializeResult,
    MetadataCatalogSpec,
    NormalizedSchema,
    ObjectStoreSpec,
    ObservabilityBackendSpec,
    PartitionSpec,
    PublishTargetSpec,
    QualityBackendSpec,
    QueryEngineSpec,
    RegulatedSurfaceSpec,
    ResourceSpec,
    RunResult,
    RunSpec,
    SchemaChange,
    SchemaMigrationPlan,
    SchemaMigrationSpec,
    TableStoreSpec,
)
from phlo.capabilities.support import CapabilitySupport, coerce_capability_support
from phlo.capabilities.telemetry import TelemetryRecorder, get_telemetry_path, iter_telemetry_events
from phlo.capabilities.workflow_wizard import (
    WorkflowApplyAction,
    WorkflowContributionMode,
    WorkflowFilePreview,
    WorkflowProposal,
    WorkflowProposalRequest,
    WorkflowStageSelection,
    WorkflowWizardContribution,
    WorkflowWizardField,
    detect_file_conflicts,
    validate_proposal_request,
)

if TYPE_CHECKING:
    from phlo.capabilities.resolver import ResolutionResult

__all__ = [
    "AlertSink",
    "AlertSinkSpec",
    "ApiBackend",
    "ApiBackendSpec",
    "AssetCheckSpec",
    "AssetSpec",
    "AuthenticatedSession",
    "AuthPrincipal",
    "AuthResult",
    "AuthenticationProvider",
    "AuthenticationProviderSpec",
    "AuthorizationDecision",
    "AuthorizationPolicyBackend",
    "AuthorizationPolicyBackendSpec",
    "BrowserLoginStart",
    "CatalogSpec",
    "CatalogScanner",
    "CatalogScannerSpec",
    "CapabilitySupport",
    "CapabilityRegistry",
    "CheckResult",
    "DataMigrationSourceSpec",
    "DecisionContext",
    "DefaultMaintenanceReadModel",
    "DefaultObservabilityBackend",
    "FieldSpec",
    "get_telemetry_path",
    "GovernanceBackendSpec",
    "LineageSinkSpec",
    "LogoutResult",
    "MaintenanceReadModel",
    "MaintenanceOperationStatus",
    "MaintenanceReadModelSpec",
    "MaintenanceStatusSnapshot",
    "MaterializeResult",
    "MetadataCatalogSpec",
    "NormalizedSchema",
    "ObjectStoreSpec",
    "ObservabilityBackend",
    "ObservabilityBackendSpec",
    "PartitionSpec",
    "Principal",
    "TraceSpan",
    "TraceSpanFilter",
    "PublishTargetSpec",
    "QueryEngine",
    "QualityBackendSpec",
    "QueryEngineSpec",
    "RegulatedSurfaceSpec",
    "RequestContext",
    "ResourceRef",
    "ResourceSpec",
    "RunResult",
    "RunSpec",
    "RuntimeContext",
    "RuntimeRouting",
    "WorkflowApplyAction",
    "WorkflowContributionMode",
    "WorkflowFilePreview",
    "WorkflowProposal",
    "WorkflowProposalRequest",
    "WorkflowStageSelection",
    "WorkflowWizardContribution",
    "WorkflowWizardField",
    "SchemaChange",
    "SchemaExtractor",
    "SchemaMigrationPlan",
    "SchemaMigrationSpec",
    "SchemaMigrator",
    "TableStoreSpec",
    "TableStore",
    "coerce_capability_support",
    "clear_capabilities",
    "configured_capability_name",
    "detect_file_conflicts",
    "get_capability_registry",
    "list_capabilities",
    "list_regulated_surfaces",
    "missing_required_capabilities",
    "register_alert_sink",
    "register_api_backend",
    "register_asset",
    "register_authorization_policy_backend",
    "register_authentication_provider",
    "register_catalog",
    "register_catalog_scanner",
    "register_check",
    "register_data_migration_source",
    "register_governance_backend",
    "register_lineage_sink",
    "register_maintenance_read_model",
    "register_metadata_catalog",
    "register_object_store",
    "register_observability_backend",
    "register_publish_target",
    "register_quality_backend",
    "register_query_engine",
    "register_regulated_surface",
    "register_resource",
    "register_schema_migrator",
    "register_default_capability_providers",
    "register_table_store",
    "ResolutionResult",
    "render_maintenance_prometheus",
    "resolve_runtime_ref",
    "resolve_capability",
    "routing_from_context",
    "TelemetryRecorder",
    "validate_proposal_request",
    "iter_telemetry_events",
    "load_maintenance_status",
]


def __getattr__(name: str):
    """Lazily expose resolver symbols to avoid circular imports."""
    if name in {
        "ResolutionResult",
        "configured_capability_name",
        "list_capabilities",
        "missing_required_capabilities",
        "resolve_capability",
    }:
        from phlo.capabilities import resolver

        return getattr(resolver, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
