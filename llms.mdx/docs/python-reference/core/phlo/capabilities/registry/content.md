# registry (/docs/python-reference/core/phlo/capabilities/registry)



Capability registry for assets, checks, and resources.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CapabilityRegistry&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/registry/CapabilityRegistry&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_capability_registry&#x22;" type="&#x22;() -> CapabilityRegistry&#x22;">
      Return the process-global capability registry instance.

      <PySourceCode>
        ```python
        def get_capability_registry() -> CapabilityRegistry:
            """Return the process-global capability registry instance.

            Returns:
                Shared in-memory capability registry.
            """

            return _GLOBAL_REGISTRY
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.registry.CapabilityRegistry&#x22;">
        Shared in-memory capability registry.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;register_asset&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an asset in the process-global registry.

      <PySourceCode>
        ```python
        def register_asset(spec: AssetSpec) -> None:
            """Register an asset in the process-global registry.

            Args:
                spec: Asset capability specification to store.
            """

            _GLOBAL_REGISTRY.register_asset(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetSpec&#x22;" value="undefined">
          Asset capability specification to store.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_check&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an asset check in the process-global registry.

      <PySourceCode>
        ```python
        def register_check(spec: AssetCheckSpec) -> None:
            """Register an asset check in the process-global registry.

            Args:
                spec: Asset check capability specification to store.
            """

            _GLOBAL_REGISTRY.register_check(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetCheckSpec&#x22;" value="undefined">
          Asset check capability specification to store.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_resource&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a resource in the process-global registry.

      <PySourceCode>
        ```python
        def register_resource(spec: ResourceSpec) -> None:
            """Register a resource in the process-global registry.

            Args:
                spec: Resource capability specification to store.
            """

            _GLOBAL_REGISTRY.register_resource(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;ResourceSpec&#x22;" value="undefined">
          Resource capability specification to store.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_table_store&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a table store in the process-global registry.

      <PySourceCode>
        ```python
        def register_table_store(spec: TableStoreSpec) -> None:
            """Register a table store in the process-global registry."""
            _GLOBAL_REGISTRY.register_table_store(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;TableStoreSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_catalog&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a catalog in the process-global registry.

      <PySourceCode>
        ```python
        def register_catalog(spec: CatalogSpec) -> None:
            """Register a catalog in the process-global registry."""
            _GLOBAL_REGISTRY.register_catalog(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;CatalogSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_catalog_scanner&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a catalog scanner in the process-global registry.

      <PySourceCode>
        ```python
        def register_catalog_scanner(spec: CatalogScannerSpec) -> None:
            """Register a catalog scanner in the process-global registry."""
            _GLOBAL_REGISTRY.register_catalog_scanner(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;CatalogScannerSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_query_engine&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a query engine in the process-global registry.

      <PySourceCode>
        ```python
        def register_query_engine(spec: QueryEngineSpec) -> None:
            """Register a query engine in the process-global registry."""
            _GLOBAL_REGISTRY.register_query_engine(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;QueryEngineSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_object_store&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an object store in the process-global registry.

      <PySourceCode>
        ```python
        def register_object_store(spec: ObjectStoreSpec) -> None:
            """Register an object store in the process-global registry."""
            _GLOBAL_REGISTRY.register_object_store(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;ObjectStoreSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_quality_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a quality backend in the process-global registry.

      <PySourceCode>
        ```python
        def register_quality_backend(spec: QualityBackendSpec) -> None:
            """Register a quality backend in the process-global registry."""
            _GLOBAL_REGISTRY.register_quality_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;QualityBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_maintenance_read_model&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a maintenance read model in the process-global registry.

      <PySourceCode>
        ```python
        def register_maintenance_read_model(spec: MaintenanceReadModelSpec) -> None:
            """Register a maintenance read model in the process-global registry."""
            _GLOBAL_REGISTRY.register_maintenance_read_model(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;MaintenanceReadModelSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_metadata_catalog&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a metadata catalog in the process-global registry.

      <PySourceCode>
        ```python
        def register_metadata_catalog(spec: MetadataCatalogSpec) -> None:
            """Register a metadata catalog in the process-global registry."""
            _GLOBAL_REGISTRY.register_metadata_catalog(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;MetadataCatalogSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_lineage_sink&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a lineage sink in the process-global registry.

      <PySourceCode>
        ```python
        def register_lineage_sink(spec: LineageSinkSpec) -> None:
            """Register a lineage sink in the process-global registry."""
            _GLOBAL_REGISTRY.register_lineage_sink(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;LineageSinkSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_governance_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a governance backend in the process-global registry.

      <PySourceCode>
        ```python
        def register_governance_backend(spec: GovernanceBackendSpec) -> None:
            """Register a governance backend in the process-global registry."""
            _GLOBAL_REGISTRY.register_governance_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;GovernanceBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_authorization_policy_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an authorization policy backend in the process-global registry.

      <PySourceCode>
        ```python
        def register_authorization_policy_backend(spec: AuthorizationPolicyBackendSpec) -> None:
            """Register an authorization policy backend in the process-global registry."""
            _GLOBAL_REGISTRY.register_authorization_policy_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;AuthorizationPolicyBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_authentication_provider&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an authentication provider in the process-global registry.

      <PySourceCode>
        ```python
        def register_authentication_provider(spec: AuthenticationProviderSpec) -> None:
            """Register an authentication provider in the process-global registry."""
            _GLOBAL_REGISTRY.register_authentication_provider(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;AuthenticationProviderSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_publish_target&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a publish target in the process-global registry.

      <PySourceCode>
        ```python
        def register_publish_target(spec: PublishTargetSpec) -> None:
            """Register a publish target in the process-global registry."""
            _GLOBAL_REGISTRY.register_publish_target(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;PublishTargetSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_alert_sink&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an alert sink in the process-global registry.

      <PySourceCode>
        ```python
        def register_alert_sink(spec: AlertSinkSpec) -> None:
            """Register an alert sink in the process-global registry."""
            _GLOBAL_REGISTRY.register_alert_sink(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;AlertSinkSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_api_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an API backend in the process-global registry.

      <PySourceCode>
        ```python
        def register_api_backend(spec: ApiBackendSpec) -> None:
            """Register an API backend in the process-global registry."""
            _GLOBAL_REGISTRY.register_api_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;ApiBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_secret_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a secret backend in the process-global registry.

      <PySourceCode>
        ```python
        def register_secret_backend(spec: SecretBackendSpec) -> None:
            """Register a secret backend in the process-global registry."""
            _GLOBAL_REGISTRY.register_secret_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;SecretBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_schema_migrator&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a schema migrator in the process-global registry.

      <PySourceCode>
        ```python
        def register_schema_migrator(spec: SchemaMigrationSpec) -> None:
            """Register a schema migrator in the process-global registry."""
            _GLOBAL_REGISTRY.register_schema_migrator(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;SchemaMigrationSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_data_migration_source&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register a data migration source adapter in the global registry.

      <PySourceCode>
        ```python
        def register_data_migration_source(spec: DataMigrationSourceSpec) -> None:
            """Register a data migration source adapter in the global registry."""
            _GLOBAL_REGISTRY.register_data_migration_source(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;DataMigrationSourceSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;register_observability_backend&#x22;" type="&#x22;(spec) -> None&#x22;">
      Register an observability backend in the global registry.

      <PySourceCode>
        ```python
        def register_observability_backend(spec: ObservabilityBackendSpec) -> None:
            """Register an observability backend in the global registry."""
            _GLOBAL_REGISTRY.register_observability_backend(spec)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec&#x22;" type="&#x22;ObservabilityBackendSpec&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;clear_capabilities&#x22;" type="&#x22;() -> None&#x22;">
      Clear all capability types from the global registry.

      <PySourceCode>
        ```python
        def clear_capabilities() -> None:
            """Clear all capability types from the global registry."""

            _GLOBAL_REGISTRY.clear()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
