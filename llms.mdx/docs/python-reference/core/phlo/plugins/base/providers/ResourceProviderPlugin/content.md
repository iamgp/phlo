# ResourceProviderPlugin (/docs/python-reference/core/phlo/plugins/base/providers/ResourceProviderPlugin)



Base class for plugins that provide resource specs.

Attributes [#attributes]

<PyAttribute name="&#x22;requires_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return required capabilities for this provider.
</PyAttribute>

<PyAttribute name="&#x22;optional_capabilities&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Return optional capabilities for this provider.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> Iterable[ResourceSpec]&#x22;">
  Return resource specifications exposed by this plugin.

  <PySourceCode>
    ```python
    @abstractmethod
    def get_resources(self) -> Iterable[ResourceSpec]:
        """Return resource specifications exposed by this plugin.

        Returns:
            Iterable of resource specifications.

        """
        raise NotImplementedError
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable&#x22;">
    Iterable of resource specifications.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_stores&#x22;" type="&#x22;(self) -> Iterable[TableStoreSpec]&#x22;">
  Return table store capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_table_stores(self) -> Iterable[TableStoreSpec]:
        """Return table store capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.TableStoreSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_catalogs&#x22;" type="&#x22;(self) -> Iterable[CatalogSpec]&#x22;">
  Return catalog capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_catalogs(self) -> Iterable[CatalogSpec]:
        """Return catalog capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.CatalogSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_catalog_scanners&#x22;" type="&#x22;(self) -> Iterable[CatalogScannerSpec]&#x22;">
  Return catalog scanner capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_catalog_scanners(self) -> Iterable[CatalogScannerSpec]:
        """Return catalog scanner capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.CatalogScannerSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_query_engines&#x22;" type="&#x22;(self) -> Iterable[QueryEngineSpec]&#x22;">
  Return query engine capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_query_engines(self) -> Iterable[QueryEngineSpec]:
        """Return query engine capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.QueryEngineSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_object_stores&#x22;" type="&#x22;(self) -> Iterable[ObjectStoreSpec]&#x22;">
  Return object-store capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_object_stores(self) -> Iterable[ObjectStoreSpec]:
        """Return object-store capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.ObjectStoreSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_quality_backends&#x22;" type="&#x22;(self) -> Iterable[QualityBackendSpec]&#x22;">
  Return quality backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_quality_backends(self) -> Iterable[QualityBackendSpec]:
        """Return quality backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.QualityBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_maintenance_read_models&#x22;" type="&#x22;(self) -> Iterable[MaintenanceReadModelSpec]&#x22;">
  Return maintenance read-model capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_maintenance_read_models(self) -> Iterable[MaintenanceReadModelSpec]:
        """Return maintenance read-model capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.MaintenanceReadModelSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_metadata_catalogs&#x22;" type="&#x22;(self) -> Iterable[MetadataCatalogSpec]&#x22;">
  Return metadata catalog capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_metadata_catalogs(self) -> Iterable[MetadataCatalogSpec]:
        """Return metadata catalog capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.MetadataCatalogSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_lineage_sinks&#x22;" type="&#x22;(self) -> Iterable[LineageSinkSpec]&#x22;">
  Return lineage sink capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_lineage_sinks(self) -> Iterable[LineageSinkSpec]:
        """Return lineage sink capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.LineageSinkSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_governance_backends&#x22;" type="&#x22;(self) -> Iterable[GovernanceBackendSpec]&#x22;">
  Return governance backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_governance_backends(self) -> Iterable[GovernanceBackendSpec]:
        """Return governance backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.GovernanceBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_authorization_policy_backends&#x22;" type="&#x22;(self) -> Iterable[AuthorizationPolicyBackendSpec]&#x22;">
  Return authorization policy backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_authorization_policy_backends(self) -> Iterable[AuthorizationPolicyBackendSpec]:
        """Return authorization policy backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.AuthorizationPolicyBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_authentication_providers&#x22;" type="&#x22;(self) -> Iterable[AuthenticationProviderSpec]&#x22;">
  Return authentication provider capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_authentication_providers(self) -> Iterable[AuthenticationProviderSpec]:
        """Return authentication provider capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.AuthenticationProviderSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_publish_targets&#x22;" type="&#x22;(self) -> Iterable[PublishTargetSpec]&#x22;">
  Return publish target capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_publish_targets(self) -> Iterable[PublishTargetSpec]:
        """Return publish target capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.PublishTargetSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_alert_sinks&#x22;" type="&#x22;(self) -> Iterable[AlertSinkSpec]&#x22;">
  Return alert sink capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_alert_sinks(self) -> Iterable[AlertSinkSpec]:
        """Return alert sink capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.AlertSinkSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_api_backends&#x22;" type="&#x22;(self) -> Iterable[ApiBackendSpec]&#x22;">
  Return API backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_api_backends(self) -> Iterable[ApiBackendSpec]:
        """Return API backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.ApiBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_secret_backends&#x22;" type="&#x22;(self) -> Iterable[SecretBackendSpec]&#x22;">
  Return secret backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_secret_backends(self) -> Iterable[SecretBackendSpec]:
        """Return secret backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.SecretBackendSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_schema_migrators&#x22;" type="&#x22;(self) -> Iterable[SchemaMigrationSpec]&#x22;">
  Return schema migrator capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_schema_migrators(self) -> Iterable[SchemaMigrationSpec]:
        """Return schema migrator capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.SchemaMigrationSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_data_migration_sources&#x22;" type="&#x22;(self) -> Iterable[DataMigrationSourceSpec]&#x22;">
  Return data migration source adapter specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_data_migration_sources(self) -> Iterable[DataMigrationSourceSpec]:
        """Return data migration source adapter specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.DataMigrationSourceSpec]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_observability_backends&#x22;" type="&#x22;(self) -> Iterable[ObservabilityBackendSpec]&#x22;">
  Return observability backend capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_observability_backends(self) -> Iterable[ObservabilityBackendSpec]:
        """Return observability backend capability specs exposed by this plugin."""
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;collections.abc.Iterable[phlo.capabilities.specs.ObservabilityBackendSpec]&#x22;" />
</PyFunction>
