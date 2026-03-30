# CapabilityRegistry (/docs/python-reference/core/phlo/capabilities/registry/CapabilityRegistry)



Thread-safe in-memory registry for capability specifications.

Attributes [#attributes]

<PyAttribute name="&#x22;assets&#x22;" type="&#x22;dict[str, AssetSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;checks&#x22;" type="&#x22;dict[tuple[str, str], AssetCheckSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;resources&#x22;" type="&#x22;dict[str, ResourceSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;table_stores&#x22;" type="&#x22;dict[str, TableStoreSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;catalogs&#x22;" type="&#x22;dict[str, CatalogSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;catalog_scanners&#x22;" type="&#x22;dict[str, CatalogScannerSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;query_engines&#x22;" type="&#x22;dict[str, QueryEngineSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;object_stores&#x22;" type="&#x22;dict[str, ObjectStoreSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;quality_backends&#x22;" type="&#x22;dict[str, QualityBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;maintenance_read_models&#x22;" type="&#x22;dict[str, MaintenanceReadModelSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;metadata_catalogs&#x22;" type="&#x22;dict[str, MetadataCatalogSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;lineage_sinks&#x22;" type="&#x22;dict[str, LineageSinkSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;governance_backends&#x22;" type="&#x22;dict[str, GovernanceBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;authorization_policy_backends&#x22;" type="&#x22;dict[str, AuthorizationPolicyBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;authentication_providers&#x22;" type="&#x22;dict[str, AuthenticationProviderSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;publish_targets&#x22;" type="&#x22;dict[str, PublishTargetSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;alert_sinks&#x22;" type="&#x22;dict[str, AlertSinkSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;api_backends&#x22;" type="&#x22;dict[str, ApiBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;secret_backends&#x22;" type="&#x22;dict[str, SecretBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;schema_migrators&#x22;" type="&#x22;dict[str, SchemaMigrationSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;data_migration_sources&#x22;" type="&#x22;dict[str, DataMigrationSourceSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

<PyAttribute name="&#x22;observability_backends&#x22;" type="&#x22;dict[str, ObservabilityBackendSpec]&#x22;" value="&#x22;field(default_factory=dict)&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;register_asset&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an asset spec by key.

  <PySourceCode>
    ```python
    def register_asset(self, spec: AssetSpec) -> None:
        """Register or replace an asset spec by key.

        Args:
            spec: Asset capability specification to store.
        """

        with self._lock:
            self.assets[spec.key] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetSpec&#x22;" value="undefined">
      Asset capability specification to store.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_check&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an asset check spec by asset/name tuple.

  <PySourceCode>
    ```python
    def register_check(self, spec: AssetCheckSpec) -> None:
        """Register or replace an asset check spec by asset/name tuple.

        Args:
            spec: Asset check capability specification to store.
        """

        with self._lock:
            self.checks[(spec.asset_key, spec.name)] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AssetCheckSpec&#x22;" value="undefined">
      Asset check capability specification to store.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_resource&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a resource spec by name.

  <PySourceCode>
    ```python
    def register_resource(self, spec: ResourceSpec) -> None:
        """Register or replace a resource spec by name.

        Args:
            spec: Resource capability specification to store.
        """

        with self._lock:
            self.resources[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;ResourceSpec&#x22;" value="undefined">
      Resource capability specification to store.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_assets&#x22;" type="&#x22;(self) -> list[AssetSpec]&#x22;">
  Return a snapshot list of all registered assets.

  <PySourceCode>
    ```python
    def list_assets(self) -> list[AssetSpec]:
        """Return a snapshot list of all registered assets.

        Returns:
            List of currently registered asset specs.
        """

        with self._lock:
            return list(self.assets.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of currently registered asset specs.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_checks&#x22;" type="&#x22;(self) -> list[AssetCheckSpec]&#x22;">
  Return a snapshot list of all registered checks.

  <PySourceCode>
    ```python
    def list_checks(self) -> list[AssetCheckSpec]:
        """Return a snapshot list of all registered checks.

        Returns:
            List of currently registered asset check specs.
        """

        with self._lock:
            return list(self.checks.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of currently registered asset check specs.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return a snapshot list of all registered resources.

  <PySourceCode>
    ```python
    def list_resources(self) -> list[ResourceSpec]:
        """Return a snapshot list of all registered resources.

        Returns:
            List of currently registered resource specs.
        """

        with self._lock:
            return list(self.resources.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of currently registered resource specs.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;register_table_store&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a table store spec by name.

  <PySourceCode>
    ```python
    def register_table_store(self, spec: TableStoreSpec) -> None:
        """Register or replace a table store spec by name."""
        with self._lock:
            self.table_stores[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;TableStoreSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_table_stores&#x22;" type="&#x22;(self) -> list[TableStoreSpec]&#x22;">
  Return a snapshot list of registered table store specs.

  <PySourceCode>
    ```python
    def list_table_stores(self) -> list[TableStoreSpec]:
        """Return a snapshot list of registered table store specs."""
        with self._lock:
            return list(self.table_stores.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.TableStoreSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_catalog&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a catalog spec by name.

  <PySourceCode>
    ```python
    def register_catalog(self, spec: CatalogSpec) -> None:
        """Register or replace a catalog spec by name."""
        with self._lock:
            self.catalogs[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;CatalogSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_catalogs&#x22;" type="&#x22;(self) -> list[CatalogSpec]&#x22;">
  Return a snapshot list of registered catalog specs.

  <PySourceCode>
    ```python
    def list_catalogs(self) -> list[CatalogSpec]:
        """Return a snapshot list of registered catalog specs."""
        with self._lock:
            return list(self.catalogs.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.CatalogSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_catalog_scanner&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a catalog scanner spec by name.

  <PySourceCode>
    ```python
    def register_catalog_scanner(self, spec: CatalogScannerSpec) -> None:
        """Register or replace a catalog scanner spec by name."""
        with self._lock:
            self.catalog_scanners[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;CatalogScannerSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_catalog_scanners&#x22;" type="&#x22;(self) -> list[CatalogScannerSpec]&#x22;">
  Return a snapshot list of registered catalog scanner specs.

  <PySourceCode>
    ```python
    def list_catalog_scanners(self) -> list[CatalogScannerSpec]:
        """Return a snapshot list of registered catalog scanner specs."""
        with self._lock:
            return list(self.catalog_scanners.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.CatalogScannerSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_query_engine&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a query engine spec by name.

  <PySourceCode>
    ```python
    def register_query_engine(self, spec: QueryEngineSpec) -> None:
        """Register or replace a query engine spec by name."""
        with self._lock:
            self.query_engines[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;QueryEngineSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_query_engines&#x22;" type="&#x22;(self) -> list[QueryEngineSpec]&#x22;">
  Return a snapshot list of registered query engine specs.

  <PySourceCode>
    ```python
    def list_query_engines(self) -> list[QueryEngineSpec]:
        """Return a snapshot list of registered query engine specs."""
        with self._lock:
            return list(self.query_engines.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.QueryEngineSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_object_store&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an object store spec by name.

  <PySourceCode>
    ```python
    def register_object_store(self, spec: ObjectStoreSpec) -> None:
        """Register or replace an object store spec by name."""
        with self._lock:
            self.object_stores[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;ObjectStoreSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_object_stores&#x22;" type="&#x22;(self) -> list[ObjectStoreSpec]&#x22;">
  Return a snapshot list of registered object store specs.

  <PySourceCode>
    ```python
    def list_object_stores(self) -> list[ObjectStoreSpec]:
        """Return a snapshot list of registered object store specs."""
        with self._lock:
            return list(self.object_stores.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.ObjectStoreSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_quality_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a quality backend spec by name.

  <PySourceCode>
    ```python
    def register_quality_backend(self, spec: QualityBackendSpec) -> None:
        """Register or replace a quality backend spec by name."""
        with self._lock:
            self.quality_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;QualityBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_quality_backends&#x22;" type="&#x22;(self) -> list[QualityBackendSpec]&#x22;">
  Return a snapshot list of registered quality backend specs.

  <PySourceCode>
    ```python
    def list_quality_backends(self) -> list[QualityBackendSpec]:
        """Return a snapshot list of registered quality backend specs."""
        with self._lock:
            return list(self.quality_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.QualityBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_maintenance_read_model&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a maintenance read-model spec by name.

  <PySourceCode>
    ```python
    def register_maintenance_read_model(self, spec: MaintenanceReadModelSpec) -> None:
        """Register or replace a maintenance read-model spec by name."""
        with self._lock:
            self.maintenance_read_models[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;MaintenanceReadModelSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_maintenance_read_models&#x22;" type="&#x22;(self) -> list[MaintenanceReadModelSpec]&#x22;">
  Return a snapshot list of maintenance read-model specs.

  <PySourceCode>
    ```python
    def list_maintenance_read_models(self) -> list[MaintenanceReadModelSpec]:
        """Return a snapshot list of maintenance read-model specs."""
        with self._lock:
            return list(self.maintenance_read_models.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.MaintenanceReadModelSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_metadata_catalog&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a metadata catalog spec by name.

  <PySourceCode>
    ```python
    def register_metadata_catalog(self, spec: MetadataCatalogSpec) -> None:
        """Register or replace a metadata catalog spec by name."""
        with self._lock:
            self.metadata_catalogs[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;MetadataCatalogSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_metadata_catalogs&#x22;" type="&#x22;(self) -> list[MetadataCatalogSpec]&#x22;">
  Return a snapshot list of registered metadata catalog specs.

  <PySourceCode>
    ```python
    def list_metadata_catalogs(self) -> list[MetadataCatalogSpec]:
        """Return a snapshot list of registered metadata catalog specs."""
        with self._lock:
            return list(self.metadata_catalogs.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.MetadataCatalogSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_lineage_sink&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a lineage sink spec by name.

  <PySourceCode>
    ```python
    def register_lineage_sink(self, spec: LineageSinkSpec) -> None:
        """Register or replace a lineage sink spec by name."""
        with self._lock:
            self.lineage_sinks[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;LineageSinkSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_lineage_sinks&#x22;" type="&#x22;(self) -> list[LineageSinkSpec]&#x22;">
  Return a snapshot list of registered lineage sink specs.

  <PySourceCode>
    ```python
    def list_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Return a snapshot list of registered lineage sink specs."""
        with self._lock:
            return list(self.lineage_sinks.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.LineageSinkSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_governance_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a governance backend spec by name.

  <PySourceCode>
    ```python
    def register_governance_backend(self, spec: GovernanceBackendSpec) -> None:
        """Register or replace a governance backend spec by name."""
        with self._lock:
            self.governance_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;GovernanceBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_governance_backends&#x22;" type="&#x22;(self) -> list[GovernanceBackendSpec]&#x22;">
  Return a snapshot list of registered governance backend specs.

  <PySourceCode>
    ```python
    def list_governance_backends(self) -> list[GovernanceBackendSpec]:
        """Return a snapshot list of registered governance backend specs."""
        with self._lock:
            return list(self.governance_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.GovernanceBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_authorization_policy_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an authorization policy backend spec by name.

  <PySourceCode>
    ```python
    def register_authorization_policy_backend(self, spec: AuthorizationPolicyBackendSpec) -> None:
        """Register or replace an authorization policy backend spec by name."""
        with self._lock:
            self.authorization_policy_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AuthorizationPolicyBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_authorization_policy_backends&#x22;" type="&#x22;(self) -> list[AuthorizationPolicyBackendSpec]&#x22;">
  Return a snapshot list of registered authorization policy backend specs.

  <PySourceCode>
    ```python
    def list_authorization_policy_backends(self) -> list[AuthorizationPolicyBackendSpec]:
        """Return a snapshot list of registered authorization policy backend specs."""
        with self._lock:
            return list(self.authorization_policy_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.AuthorizationPolicyBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_authentication_provider&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an authentication provider spec by name.

  <PySourceCode>
    ```python
    def register_authentication_provider(self, spec: AuthenticationProviderSpec) -> None:
        """Register or replace an authentication provider spec by name."""
        with self._lock:
            self.authentication_providers[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AuthenticationProviderSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_authentication_providers&#x22;" type="&#x22;(self) -> list[AuthenticationProviderSpec]&#x22;">
  Return a snapshot list of registered authentication provider specs.

  <PySourceCode>
    ```python
    def list_authentication_providers(self) -> list[AuthenticationProviderSpec]:
        """Return a snapshot list of registered authentication provider specs."""
        with self._lock:
            return list(self.authentication_providers.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.AuthenticationProviderSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_publish_target&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a publish target spec by name.

  <PySourceCode>
    ```python
    def register_publish_target(self, spec: PublishTargetSpec) -> None:
        """Register or replace a publish target spec by name."""
        with self._lock:
            self.publish_targets[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;PublishTargetSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_publish_targets&#x22;" type="&#x22;(self) -> list[PublishTargetSpec]&#x22;">
  Return a snapshot list of registered publish target specs.

  <PySourceCode>
    ```python
    def list_publish_targets(self) -> list[PublishTargetSpec]:
        """Return a snapshot list of registered publish target specs."""
        with self._lock:
            return list(self.publish_targets.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.PublishTargetSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_alert_sink&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an alert sink spec by name.

  <PySourceCode>
    ```python
    def register_alert_sink(self, spec: AlertSinkSpec) -> None:
        """Register or replace an alert sink spec by name."""
        with self._lock:
            self.alert_sinks[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;AlertSinkSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_alert_sinks&#x22;" type="&#x22;(self) -> list[AlertSinkSpec]&#x22;">
  Return a snapshot list of registered alert sink specs.

  <PySourceCode>
    ```python
    def list_alert_sinks(self) -> list[AlertSinkSpec]:
        """Return a snapshot list of registered alert sink specs."""
        with self._lock:
            return list(self.alert_sinks.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.AlertSinkSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_api_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an API backend spec by name.

  <PySourceCode>
    ```python
    def register_api_backend(self, spec: ApiBackendSpec) -> None:
        """Register or replace an API backend spec by name."""
        with self._lock:
            self.api_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;ApiBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_api_backends&#x22;" type="&#x22;(self) -> list[ApiBackendSpec]&#x22;">
  Return a snapshot list of registered API backend specs.

  <PySourceCode>
    ```python
    def list_api_backends(self) -> list[ApiBackendSpec]:
        """Return a snapshot list of registered API backend specs."""
        with self._lock:
            return list(self.api_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.ApiBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_secret_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a secret backend spec by name.

  <PySourceCode>
    ```python
    def register_secret_backend(self, spec: SecretBackendSpec) -> None:
        """Register or replace a secret backend spec by name."""
        with self._lock:
            self.secret_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;SecretBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_secret_backends&#x22;" type="&#x22;(self) -> list[SecretBackendSpec]&#x22;">
  Return a snapshot list of registered secret backend specs.

  <PySourceCode>
    ```python
    def list_secret_backends(self) -> list[SecretBackendSpec]:
        """Return a snapshot list of registered secret backend specs."""
        with self._lock:
            return list(self.secret_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.SecretBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_schema_migrator&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a schema migrator spec by name.

  <PySourceCode>
    ```python
    def register_schema_migrator(self, spec: SchemaMigrationSpec) -> None:
        """Register or replace a schema migrator spec by name."""
        with self._lock:
            self.schema_migrators[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;SchemaMigrationSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_schema_migrators&#x22;" type="&#x22;(self) -> list[SchemaMigrationSpec]&#x22;">
  Return a snapshot list of registered schema migrator specs.

  <PySourceCode>
    ```python
    def list_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Return a snapshot list of registered schema migrator specs."""
        with self._lock:
            return list(self.schema_migrators.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.SchemaMigrationSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_data_migration_source&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace a data migration source adapter spec by name.

  <PySourceCode>
    ```python
    def register_data_migration_source(self, spec: DataMigrationSourceSpec) -> None:
        """Register or replace a data migration source adapter spec by name."""
        with self._lock:
            self.data_migration_sources[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;DataMigrationSourceSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_data_migration_sources&#x22;" type="&#x22;(self) -> list[DataMigrationSourceSpec]&#x22;">
  Return a snapshot list of registered migration source adapter specs.

  <PySourceCode>
    ```python
    def list_data_migration_sources(self) -> list[DataMigrationSourceSpec]:
        """Return a snapshot list of registered migration source adapter specs."""
        with self._lock:
            return list(self.data_migration_sources.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.DataMigrationSourceSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;register_observability_backend&#x22;" type="&#x22;(self, spec) -> None&#x22;">
  Register or replace an observability backend spec by name.

  <PySourceCode>
    ```python
    def register_observability_backend(self, spec: ObservabilityBackendSpec) -> None:
        """Register or replace an observability backend spec by name."""
        with self._lock:
            self.observability_backends[spec.name] = spec
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;spec&#x22;" type="&#x22;ObservabilityBackendSpec&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_observability_backends&#x22;" type="&#x22;(self) -> list[ObservabilityBackendSpec]&#x22;">
  Return a snapshot list of registered observability backend specs.

  <PySourceCode>
    ```python
    def list_observability_backends(self) -> list[ObservabilityBackendSpec]:
        """Return a snapshot list of registered observability backend specs."""
        with self._lock:
            return list(self.observability_backends.values())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[phlo.capabilities.specs.ObservabilityBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;clear&#x22;" type="&#x22;(self) -> None&#x22;">
  Remove all assets, checks, and resources from the registry.

  <PySourceCode>
    ```python
    def clear(self) -> None:
        """Remove all assets, checks, and resources from the registry."""

        with self._lock:
            self.assets.clear()
            self.checks.clear()
            self.resources.clear()
            self.table_stores.clear()
            self.catalogs.clear()
            self.catalog_scanners.clear()
            self.query_engines.clear()
            self.object_stores.clear()
            self.quality_backends.clear()
            self.maintenance_read_models.clear()
            self.metadata_catalogs.clear()
            self.lineage_sinks.clear()
            self.governance_backends.clear()
            self.authorization_policy_backends.clear()
            self.authentication_providers.clear()
            self.publish_targets.clear()
            self.alert_sinks.clear()
            self.api_backends.clear()
            self.secret_backends.clear()
            self.schema_migrators.clear()
            self.data_migration_sources.clear()
            self.observability_backends.clear()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;clear_checks&#x22;" type="&#x22;(self) -> None&#x22;">
  Remove all registered checks while preserving assets/resources.

  <PySourceCode>
    ```python
    def clear_checks(self) -> None:
        """Remove all registered checks while preserving assets/resources."""

        with self._lock:
            self.checks.clear()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, assets=dict(), checks=dict(), resources=dict(), table_stores=dict(), catalogs=dict(), catalog_scanners=dict(), query_engines=dict(), object_stores=dict(), quality_backends=dict(), maintenance_read_models=dict(), metadata_catalogs=dict(), lineage_sinks=dict(), governance_backends=dict(), authorization_policy_backends=dict(), authentication_providers=dict(), publish_targets=dict(), alert_sinks=dict(), api_backends=dict(), secret_backends=dict(), schema_migrators=dict(), data_migration_sources=dict(), observability_backends=dict()) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;assets&#x22;" type="&#x22;dict[str, AssetSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;dict[tuple[str, str], AssetCheckSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;resources&#x22;" type="&#x22;dict[str, ResourceSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;table_stores&#x22;" type="&#x22;dict[str, TableStoreSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;catalogs&#x22;" type="&#x22;dict[str, CatalogSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;catalog_scanners&#x22;" type="&#x22;dict[str, CatalogScannerSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;query_engines&#x22;" type="&#x22;dict[str, QueryEngineSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;object_stores&#x22;" type="&#x22;dict[str, ObjectStoreSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;quality_backends&#x22;" type="&#x22;dict[str, QualityBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;maintenance_read_models&#x22;" type="&#x22;dict[str, MaintenanceReadModelSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;metadata_catalogs&#x22;" type="&#x22;dict[str, MetadataCatalogSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;lineage_sinks&#x22;" type="&#x22;dict[str, LineageSinkSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;governance_backends&#x22;" type="&#x22;dict[str, GovernanceBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;authorization_policy_backends&#x22;" type="&#x22;dict[str, AuthorizationPolicyBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;authentication_providers&#x22;" type="&#x22;dict[str, AuthenticationProviderSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;publish_targets&#x22;" type="&#x22;dict[str, PublishTargetSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;alert_sinks&#x22;" type="&#x22;dict[str, AlertSinkSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;api_backends&#x22;" type="&#x22;dict[str, ApiBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;secret_backends&#x22;" type="&#x22;dict[str, SecretBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;schema_migrators&#x22;" type="&#x22;dict[str, SchemaMigrationSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;data_migration_sources&#x22;" type="&#x22;dict[str, DataMigrationSourceSpec]&#x22;" value="&#x22;dict()&#x22;" />

    <PyParameter name="&#x22;observability_backends&#x22;" type="&#x22;dict[str, ObservabilityBackendSpec]&#x22;" value="&#x22;dict()&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
