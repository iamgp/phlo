# HasuraServicePlugin (/docs/python-reference/packages/phlo-hasura/phlo_hasura/plugin/HasuraServicePlugin)



Service plugin for Hasura GraphQL engine.

Integrates Hasura with the Phlo service management system, providing
Docker service definitions and metadata for the GraphQL API engine.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the Hasura service.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = HasuraServicePlugin()
    > > > meta = plugin.metadata
    > > > print(meta.name, meta.version)
    > > > hasura 0.1.0
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return the Docker service definition for Hasura.

  Loads the service.yaml file from the package resources and
  returns it as a parsed dictionary. This defines the Docker
  Compose service configuration for the Hasura container.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = HasuraServicePlugin()
    > > > service = plugin.service\_definition
    > > > print(service\['services']\['hasura']\['image'])
    > > > hasura/graphql-engine:latest
  </Callout>
</PyAttribute>
