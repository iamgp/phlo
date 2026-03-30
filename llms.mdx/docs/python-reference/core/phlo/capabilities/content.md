# capabilities (/docs/python-reference/core/phlo/capabilities)



Capability primitives and registry for Phlo.

This module provides the capability system that enables runtime feature discovery
and dependency injection. Capabilities abstract concrete implementations of
features like query engines, table stores, and authentication providers.

The capability system allows Phlo to:

* Register and discover implementations at runtime
* Resolve capabilities based on configuration and availability
* Provide a unified interface for diverse backends
* Support plugin-based extensibility

Key Concepts:

* **Capability**: An abstract feature (e.g., "query\_engine")
* **Provider**: A concrete implementation (e.g., TrinoQueryEngine)
* **Specification**: Configuration for a capability instance
* **Registry**: Thread-safe storage for capability specifications
* **Resolution**: Selecting the best available provider

Capability Types:

* `query_engine`: SQL query execution (Trino, DuckDB, etc.)
* `table_store`: Table storage (Iceberg, Delta, etc.)
* `catalog`: Metadata catalog (Nessie, OpenMetadata, etc.)
* `object_store`: Object storage (MinIO, S3, etc.)
* `authentication`: User authentication providers
* `authorization`: Policy-based access control
* `observability`: Metrics and monitoring backends
* `alert_sink`: Alert notification destinations
* `quality_backend`: Data quality validation
* `schema_migrator`: Schema evolution management
* `maintenance_read_model`: Maintenance status tracking

Main Components:

* :class:`CapabilityRegistry`: Thread-safe capability storage
* :func:`get_capability_registry`: Access the global registry
* :func:`resolve_capability`: Resolve a capability to a provider
* :func:`register_*`: Functions to register capability implementations
* :class:`CapabilitySupport`: Declare operational guarantees
* :class:`RuntimeContext`: Context for capability resolution

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
        metadata=\{"default_catalog": "iceberg"\}
    )
)

# Resolve the best available query engine
result = resolve_capability("query_engine")
if result:
    engine: QueryEngine = result.provider
    rows = engine.execute("SELECT * FROM iceberg.my_table")
```

See Also:

* :mod:`phlo.plugins.base`: Plugin base classes using capabilities
* :mod:`phlo.capabilities.registry`: Capability registration
* :mod:`phlo.capabilities.resolver`: Capability resolution
* :mod:`phlo.capabilities.specs`: Capability specifications
* :mod:`phlo.capabilities.interfaces`: Capability interfaces

Note:
This module uses lazy loading for resolver functions to prevent
circular imports during plugin discovery.

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['AlertSink', 'AlertSinkSpec', 'ApiBackend', 'ApiBackendSpec', 'AssetCheckSpec', 'AssetSpec', 'AuthenticatedSession', 'AuthPrincipal', 'AuthResult', 'AuthenticationProvider', 'AuthenticationProviderSpec', 'AuthorizationDecision', 'AuthorizationPolicyBackend', 'AuthorizationPolicyBackendSpec', 'BrowserLoginStart', 'CatalogSpec', 'CatalogScanner', 'CatalogScannerSpec', 'CapabilitySupport', 'CapabilityRegistry', 'CheckResult', 'DataMigrationSourceSpec', 'DecisionContext', 'DefaultMaintenanceReadModel', 'DefaultObservabilityBackend', 'FieldSpec', 'get_telemetry_path', 'GovernanceBackendSpec', 'LineageSinkSpec', 'LogoutResult', 'MaintenanceReadModel', 'MaintenanceOperationStatus', 'MaintenanceReadModelSpec', 'MaintenanceStatusSnapshot', 'MaterializeResult', 'MetadataCatalogSpec', 'NormalizedSchema', 'ObjectStoreSpec', 'ObservabilityBackend', 'ObservabilityBackendSpec', 'PartitionSpec', 'Principal', 'PublishTargetSpec', 'QueryEngine', 'QualityBackendSpec', 'QueryEngineSpec', 'RequestContext', 'ResourceRef', 'ResourceSpec', 'RunResult', 'RunSpec', 'RuntimeContext', 'RuntimeRouting', 'SchemaChange', 'SchemaExtractor', 'SchemaMigrationPlan', 'SchemaMigrationSpec', 'SchemaMigrator', 'TableStoreSpec', 'TableStore', 'coerce_capability_support', 'clear_capabilities', 'configured_capability_name', 'get_capability_registry', 'list_capabilities', 'missing_required_capabilities', 'register_alert_sink', 'register_api_backend', 'register_asset', 'register_authorization_policy_backend', 'register_authentication_provider', 'register_catalog', 'register_catalog_scanner', 'register_check', 'register_data_migration_source', 'register_governance_backend', 'register_lineage_sink', 'register_maintenance_read_model', 'register_metadata_catalog', 'register_object_store', 'register_observability_backend', 'register_publish_target', 'register_quality_backend', 'register_query_engine', 'register_resource', 'register_schema_migrator', 'register_default_capability_providers', 'register_table_store', 'ResolutionResult', 'render_maintenance_prometheus', 'resolve_runtime_ref', 'resolve_capability', 'routing_from_context', 'TelemetryRecorder', 'iter_telemetry_events', 'load_maintenance_status']&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;__getattr__&#x22;" type="&#x22;(name)&#x22;">
      Lazily expose resolver symbols to avoid circular imports.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/specs&#x22;" title="&#x22;specs&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/maintenance&#x22;" title="&#x22;maintenance&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/runtime&#x22;" title="&#x22;runtime&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/authentication&#x22;" title="&#x22;authentication&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/telemetry&#x22;" title="&#x22;telemetry&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/authorization&#x22;" title="&#x22;authorization&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/support&#x22;" title="&#x22;support&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/resolver&#x22;" title="&#x22;resolver&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/interfaces&#x22;" title="&#x22;interfaces&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/authorization_opa&#x22;" title="&#x22;authorization_opa&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/registry&#x22;" title="&#x22;registry&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/observability&#x22;" title="&#x22;observability&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/schema&#x22;" title="&#x22;schema&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities/discovery&#x22;" title="&#x22;discovery&#x22;" />
    </Cards>
  </Tab>
</Tabs>
