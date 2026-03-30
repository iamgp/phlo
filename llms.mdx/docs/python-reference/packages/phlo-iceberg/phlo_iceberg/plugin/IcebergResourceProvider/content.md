# IcebergResourceProvider (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/plugin/IcebergResourceProvider)



Resource provider plugin for Iceberg/Nessie catalog access.

Registers Iceberg capabilities with Phlo's plugin system, providing:

* Table storage via `IcebergResource`
* Schema migration via `IcebergSchemaMigrator`

The plugin advertises full Iceberg capability support for versioning,
snapshots, and schema evolution.

Example:
Plugin registration::

Plugin is auto-registered via entry points [#plugin-is-auto-registered-via-entry-points]

In pyproject.toml: [#in-pyprojecttoml]

\[project.entry-points."phlo.resource\_providers"]
iceberg = "phlo\_iceberg.plugin:IcebergResourceProvider"

Access resources::

from phlo.plugins import get\_resource\_provider

provider = get\_resource\_provider("iceberg")
resources = provider.get\_resources()

Get table store [#get-table-store]

table\_store = provider.get\_table\_stores()\[0]
resource = table\_store.provider

Use resource [#use-resource]

resource.append\_parquet("raw\.events", "/data/events.parquet")

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Get plugin metadata.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Check plugin capabilities::

    provider = IcebergResourceProvider()
    meta = provider.metadata

    print(f"Plugin: \{meta.name} v\{meta.version}")
    print(f"Supports refs: \{meta.support.supports\_refs}")
    print(f"Supports snapshots: \{meta.support.supports\_snapshots}")
  </Callout>
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Get resource specs exposed by this plugin.

  Returns the primary Iceberg resource for table operations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Get resources::

    provider = IcebergResourceProvider()
    specs = provider.get\_resources()

    for spec in specs:
    print(f"Resource: \{spec.name}")

    Use spec.resource for table operations [#use-specresource-for-table-operations]
  </Callout>

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Get resource specs exposed by this plugin.

        Returns the primary Iceberg resource for table operations.

        Returns:
            list[ResourceSpec]: Resource specifications containing
                ``IcebergResource`` instances.

        Example:
            Get resources::

                provider = IcebergResourceProvider()
                specs = provider.get_resources()

                for spec in specs:
                    print(f"Resource: {spec.name}")
                    # Use spec.resource for table operations

        """
        return [ResourceSpec(name="table_store", resource=IcebergResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ResourceSpec]: Resource specifications containing
    `IcebergResource` instances.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_stores&#x22;" type="&#x22;(self) -> list[TableStoreSpec]&#x22;">
  Get table-store capability specs exposed by this plugin.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Get table store capabilities::

    provider = IcebergResourceProvider()
    stores = provider.get\_table\_stores()

    for store in stores:
    print(f"Store: \{store.name}")
    print(f"Supports refs: \{store.support.supports\_refs}")

    Access store.provider for IcebergResource [#access-storeprovider-for-icebergresource]
  </Callout>

  <PySourceCode>
    ```python
    def get_table_stores(self) -> list[TableStoreSpec]:
        """Get table-store capability specs exposed by this plugin.

        Returns:
            list[TableStoreSpec]: Table store specifications with
                full Iceberg capability support.

        Example:
            Get table store capabilities::

                provider = IcebergResourceProvider()
                stores = provider.get_table_stores()

                for store in stores:
                    print(f"Store: {store.name}")
                    print(f"Supports refs: {store.support.supports_refs}")
                    # Access store.provider for IcebergResource

        """
        return [
            TableStoreSpec(
                name="iceberg",
                provider=IcebergResource(),
                support=CapabilitySupport(
                    supports_refs=True,
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
    list\[TableStoreSpec]: Table store specifications with
    full Iceberg capability support.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_schema_migrators&#x22;" type="&#x22;(self) -> list[SchemaMigrationSpec]&#x22;">
  Get schema-migrator capability specs exposed by this plugin.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Get schema migrator::

    provider = IcebergResourceProvider()
    migrators = provider.get\_schema\_migrators()

    for migrator in migrators:
    print(f"Migrator: \{migrator.name}")

    Use migrator.provider for schema operations [#use-migratorprovider-for-schema-operations]

    migrator.provider.diff_schema(...) [#migratorproviderdiff_schema]
  </Callout>

  <PySourceCode>
    ```python
    def get_schema_migrators(self) -> list[SchemaMigrationSpec]:
        """Get schema-migrator capability specs exposed by this plugin.

        Returns:
            list[SchemaMigrationSpec]: Schema migration specifications
                using ``IcebergSchemaMigrator``.

        Example:
            Get schema migrator::

                provider = IcebergResourceProvider()
                migrators = provider.get_schema_migrators()

                for migrator in migrators:
                    print(f"Migrator: {migrator.name}")
                    # Use migrator.provider for schema operations
                    # migrator.provider.diff_schema(...)

        """
        return [
            SchemaMigrationSpec(
                name="iceberg",
                provider=IcebergSchemaMigrator(),
                support=CapabilitySupport(supports_schema_evolution=True),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[SchemaMigrationSpec]: Schema migration specifications
    using `IcebergSchemaMigrator`.
  </PyFunctionReturn>
</PyFunction>
