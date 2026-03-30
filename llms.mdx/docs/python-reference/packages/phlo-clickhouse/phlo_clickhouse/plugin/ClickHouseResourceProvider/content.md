# ClickHouseResourceProvider (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseResourceProvider)



Resource provider plugin for ClickHouse.

Provides ClickHouse resources, table stores, query engines, and
publish targets to the Phlo capability framework.

Example:

> > > provider = ClickHouseResourceProvider()
> > > resources = provider.get\_resources()
> > > len(resources)
> > > 1

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for resource provider registration.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return list of ClickHouse resource specifications.

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Return list of ClickHouse resource specifications.

        Returns:
            List containing a ResourceSpec for the ClickHouse resource.

        """
        return [ResourceSpec(name="clickhouse", resource=ClickHouseResource())]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a ResourceSpec for the ClickHouse resource.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_table_stores&#x22;" type="&#x22;(self) -> list[TableStoreSpec]&#x22;">
  Return list of ClickHouse table store specifications.

  <PySourceCode>
    ```python
    def get_table_stores(self) -> list[TableStoreSpec]:
        """Return list of ClickHouse table store specifications.

        Returns:
            List containing a TableStoreSpec for ClickHouse with
            capability flags for schema evolution support.

        """
        return [
            TableStoreSpec(
                name="clickhouse",
                provider=ClickHouseResource(),
                support=CapabilitySupport(
                    supports_snapshots=False,
                    supports_schema_evolution=True,
                ),
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a TableStoreSpec for ClickHouse with
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_query_engines&#x22;" type="&#x22;(self) -> list[QueryEngineSpec]&#x22;">
  Return list of ClickHouse query engine specifications.

  Reads current settings to populate connection metadata including
  host, port, and database information.

  <PySourceCode>
    ```python
    def get_query_engines(self) -> list[QueryEngineSpec]:
        """Return list of ClickHouse query engine specifications.

        Reads current settings to populate connection metadata including
        host, port, and database information.

        Returns:
            List containing a QueryEngineSpec for ClickHouse with
            full connection metadata and capability support flags.

        """
        settings = get_clickhouse_settings()
        return [
            QueryEngineSpec(
                name="clickhouse",
                provider=ClickHouseResource(),
                metadata={
                    "host": settings.clickhouse_host,
                    "port": settings.clickhouse_http_port,
                    "native_port": settings.clickhouse_native_port,
                    "default_database": settings.clickhouse_db,
                    "service_type": "ClickHouse",
                },
                support=CLICKHOUSE_QUERY_ENGINE_SUPPORT,
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a QueryEngineSpec for ClickHouse with
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_publish_targets&#x22;" type="&#x22;(self) -> list[PublishTargetSpec]&#x22;">
  Return list of ClickHouse publish target specifications.

  <PySourceCode>
    ```python
    def get_publish_targets(self) -> list[PublishTargetSpec]:
        """Return list of ClickHouse publish target specifications.

        Returns:
            List containing a PublishTargetSpec for the ClickHouse
            data mart publishing target.

        """
        return [
            PublishTargetSpec(
                name="clickhouse",
                provider=ClickHousePublishTarget(),
                metadata={"target_system": "clickhouse", "role": "serving"},
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List containing a PublishTargetSpec for the ClickHouse
  </PyFunctionReturn>
</PyFunction>
