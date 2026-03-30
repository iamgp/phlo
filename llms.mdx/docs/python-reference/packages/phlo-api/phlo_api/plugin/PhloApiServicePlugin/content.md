# PhloApiServicePlugin (/docs/python-reference/packages/phlo-api/phlo_api/plugin/PhloApiServicePlugin)



Service plugin for the Phlo API backend.

This plugin registers the Phlo API as a discoverable service within
the phlo ecosystem. It provides metadata about the service and
exposes the Docker Compose service definition.

The plugin reads its service definition from the embedded service.yaml
file within the phlo\_api package.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Plugin metadata including name, version, and description.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Docker Compose service configuration dict.
</PyAttribute>
