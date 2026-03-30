# DeltaResourceProvider (/docs/python-reference/packages/phlo-delta/phlo_delta/plugin/DeltaResourceProvider)



Resource provider plugin for Delta Lake access.

This plugin exposes Delta Lake resources to the Phlo framework,
providing table storage, schema migration, and time travel capabilities.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin metadata including name, version, and capabilities.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Get resource specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Get resource specs exposed by this plugin.

        Returns:
            list[ResourceSpec]: Delta resource specifications containing
                the DeltaResource instance.

        """
        return [ResourceSpec(name="table_store", resource=DeltaResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ResourceSpec]: Delta resource specifications containing
    the DeltaResource instance.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_stores&#x22;" type="&#x22;(self) -> list[TableStoreSpec]&#x22;">
  Get table-store capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_table_stores(self) -> list[TableStoreSpec]:
        """Get table-store capability specs exposed by this plugin.

        Returns:
            list[TableStoreSpec]: Delta table-store capability specifications
                with snapshot, schema evolution, and time travel support.

        """
        return [
            TableStoreSpec(
                name="delta",
                provider=DeltaResource(),
                support=CapabilitySupport(
                    supports_snapshots=True,
                    supports_schema_evolution=True,
                    supports_time_travel=True,
                ),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[TableStoreSpec]: Delta table-store capability specifications
    with snapshot, schema evolution, and time travel support.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_migrators&#x22;" type="&#x22;(self) -> list[SchemaMigrationSpec]&#x22;">
  Get schema-migrator capability specs exposed by this plugin.

  <PySourceCode>
    ```python
    def get_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Get schema-migrator capability specs exposed by this plugin.

        Returns:
            list[SchemaMigrationSpec]: Delta schema migrator specifications
                with schema evolution support.

        """
        return [
            SchemaMigrationSpec(
                name="delta",
                provider=DeltaSchemaMigrator(),
                support=CapabilitySupport(supports_schema_evolution=True),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[SchemaMigrationSpec]: Delta schema migrator specifications
    with schema evolution support.
  </PyFunctionReturn>
</PyFunction>
