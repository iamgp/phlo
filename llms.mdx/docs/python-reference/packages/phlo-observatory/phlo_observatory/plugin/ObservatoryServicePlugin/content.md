# ObservatoryServicePlugin (/docs/python-reference/packages/phlo-observatory/phlo_observatory/plugin/ObservatoryServicePlugin)



Service plugin for the Observatory UI container orchestration.

This plugin integrates the Observatory web interface with Phlo's service
management system, enabling deployment via Docker Compose.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin metadata including name, version, description, and tags.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Parsed Docker Compose service configuration.
</PyAttribute>
