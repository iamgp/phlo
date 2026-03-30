# ClickHouseServicePlugin (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/plugin/ClickHouseServicePlugin)



Service plugin for ClickHouse database service.

Manages the ClickHouse database service lifecycle within Phlo's
service orchestration framework.

Example:

> > > plugin = ClickHouseServicePlugin()
> > > plugin.metadata.name
> > > 'clickhouse'

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for service registration.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return Docker Compose service definition for ClickHouse.
</PyAttribute>
