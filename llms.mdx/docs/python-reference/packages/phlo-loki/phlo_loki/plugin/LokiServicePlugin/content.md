# LokiServicePlugin (/docs/python-reference/packages/phlo-loki/phlo_loki/plugin/LokiServicePlugin)



Service plugin for Loki log aggregation.

This plugin manages the lifecycle of a Loki container for log aggregation
and querying within the Phlo platform. It provides Docker Compose service
configuration loaded from package resources.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the Loki service.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the Loki service definition from package resources.
</PyAttribute>
