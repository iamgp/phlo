# GrafanaServicePlugin (/docs/python-reference/packages/phlo-grafana/phlo_grafana/plugin/GrafanaServicePlugin)



Service plugin for Grafana visualization and dashboards.

This plugin registers Grafana as a managed service within the Phlo
ecosystem, providing metrics visualization capabilities. It loads service
configuration from a local YAML file and exposes metadata for service
discovery and management.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for Grafana service registration.

  Provides essential metadata about the Grafana plugin including its
  name, version, description, author, and categorization tags for
  service discovery and management interfaces.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = GrafanaServicePlugin()
    > > > meta = plugin.metadata
    > > > assert "observability" in meta.tags
    > > > assert meta.name == "grafana"
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load and return the Grafana service definition from YAML.

  Reads the service.yaml file from the package resources using
  importlib.resources, ensuring the configuration is accessible
  regardless of how the package is installed (wheel, sdist, etc.).

  The service definition typically contains Docker Compose configuration
  for running Grafana with appropriate networking, volumes, and
  environment settings.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > plugin = GrafanaServicePlugin()
    > > > definition = plugin.service\_definition
    > > > services = definition.get('services', \{})
    > > > grafana\_service = services.get('grafana', \{})
    > > > image = grafana\_service.get('image', '')
  </Callout>
</PyAttribute>
