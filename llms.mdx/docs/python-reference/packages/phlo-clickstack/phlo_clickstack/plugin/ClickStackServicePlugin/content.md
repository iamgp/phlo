# ClickStackServicePlugin (/docs/python-reference/packages/phlo-clickstack/phlo_clickstack/plugin/ClickStackServicePlugin)



Service plugin for ClickStack.

Provides ClickStack (ClickHouse-based observability backend) as a
managed service within the Phlo services framework. The service
definition is loaded from the bundled service.yaml file.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for ClickStack service registration.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  ClickStack Docker Compose configuration.
</PyAttribute>
