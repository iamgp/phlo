# PrometheusServicePlugin (/docs/python-reference/packages/phlo-prometheus/phlo_prometheus/plugin/PrometheusServicePlugin)



Service plugin for Prometheus metrics collection and monitoring.

This plugin provides Prometheus service configuration for Docker Compose
deployment within the Phlo platform. It loads service definitions from
embedded YAML resources and exposes them through the standard ServicePlugin
interface.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the Prometheus service.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PrometheusServicePlugin()
    > > > meta = plugin.metadata
    > > > meta.name
    > > > 'prometheus'
    > > > 'observability' in meta.tags
    > > > True
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Return the Docker service definition for Prometheus.

  Loads the service definition from the embedded service.yaml resource
  file. This includes container configuration, ports, volumes, and
  networking for the Prometheus metrics server.

  Performance metrics are logged for observability, including load time
  and service count.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = PrometheusServicePlugin()
    > > > definition = plugin.service\_definition
    > > > 'services' in definition
    > > > True
    > > > isinstance(definition.get('services'), dict)
    > > > True
  </Callout>
</PyAttribute>
