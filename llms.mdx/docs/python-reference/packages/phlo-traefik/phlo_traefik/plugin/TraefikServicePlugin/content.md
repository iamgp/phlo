# TraefikServicePlugin (/docs/python-reference/packages/phlo-traefik/phlo_traefik/plugin/TraefikServicePlugin)



Service plugin for Traefik reverse proxy.

This plugin provides integration with Traefik, a modern HTTP reverse proxy
and load balancer, enabling local service discovery and routing within the
Phlo platform.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for Traefik service registration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = TraefikServicePlugin()
    > > > metadata = plugin.metadata
    > > > print(metadata.name)
    > > > 'traefik'
    > > > print(metadata.version)
    > > > '0.1.0'
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load and return the Traefik service definition.

  Reads the service.yaml configuration file from the package resources
  and returns it as a parsed Python dictionary.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = TraefikServicePlugin()
    > > > definition = plugin.service\_definition
    > > > print(definition\['services'].keys())
  </Callout>
</PyAttribute>
