# ClickHouseSetupServicePlugin (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseSetupServicePlugin)



Service plugin for ClickHouse database initialization.

Handles the initial setup and database creation for ClickHouse
during the Phlo services initialization phase.

Example:

> > > plugin = ClickHouseSetupServicePlugin()
> > > plugin.metadata.name
> > > 'clickhouse-setup'

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for setup service registration.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return Docker Compose service definition for ClickHouse setup.
</PyAttribute>
