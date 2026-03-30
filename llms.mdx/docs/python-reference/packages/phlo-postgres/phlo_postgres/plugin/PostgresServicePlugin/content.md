# PostgresServicePlugin (/docs/python-reference/packages/phlo-postgres/phlo_postgres/plugin/PostgresServicePlugin)



Service plugin for managing PostgreSQL as a phlo service.

This plugin provides the core PostgreSQL database service definition for
docker-compose integration. It loads service configuration from package
data (service.yaml) and exposes metadata for plugin discovery.

Example:

> > > plugin = PostgresServicePlugin()
> > > metadata = plugin.metadata
> > > print(f"Service: \{metadata.name} v\{metadata.version}")
> > > Service: postgres v0.1.0
> > > definition = plugin.service\_definition

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the PostgreSQL service.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresServicePlugin()
    > > > meta = plugin.metadata
    > > > print(meta.name)
    > > > postgres
    > > > print(meta.tags)
    > > > \['core', 'database', 'postgres']
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the PostgreSQL service definition from package data.

  Reads and parses the service.yaml file from the package resources,
  returning a dictionary suitable for docker-compose configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PostgresServicePlugin()
    > > > definition = plugin.service\_definition
    > > > print(definition.keys())
    > > > dict\_keys(\['services', ...])
  </Callout>
</PyAttribute>
