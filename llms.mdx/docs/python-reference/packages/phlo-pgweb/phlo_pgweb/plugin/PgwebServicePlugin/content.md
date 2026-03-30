# PgwebServicePlugin (/docs/python-reference/packages/phlo-pgweb/phlo_pgweb/plugin/PgwebServicePlugin)



Service plugin for pgweb PostgreSQL web UI.

This plugin provides integration with pgweb, a lightweight web-based
PostgreSQL admin tool. It reads service configuration from a bundled
service.yaml file and exposes standard Phlo plugin metadata.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the pgweb service.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PgwebServicePlugin()
    > > > meta = plugin.metadata
    > > > meta.name
    > > > 'pgweb'
    > > > meta.tags
    > > > \['admin', 'postgres', 'ui']
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return the Docker service definition for pgweb.

  Reads and parses the service.yaml file bundled with the package
  to provide the Docker Compose service configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PgwebServicePlugin()
    > > > definition = plugin.service\_definition
    > > > 'services' in definition
    > > > True
  </Callout>
</PyAttribute>
