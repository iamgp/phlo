# AlloyServicePlugin (/docs/python-reference/packages/phlo-alloy/phlo_alloy/plugin/AlloyServicePlugin)



Service plugin for Grafana Alloy log collection and shipping.

This plugin manages the Grafana Alloy service lifecycle within the Phlo platform.
Alloy collects logs from various sources and ships them to Loki for centralized
storage and analysis. The plugin provides metadata for discovery and loads the
service configuration from embedded YAML resources.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return plugin metadata for the Alloy service.

  Provides static metadata used by the Phlo plugin discovery system to
  identify and categorize the Alloy service plugin. This includes the
  plugin name, version, description, author information, and searchable tags.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Metadata is accessed by the plugin discovery system::

    plugin = AlloyServicePlugin()
    meta = plugin.metadata
    print(f"\{meta.name} v\{meta.version}: \{meta.description}")

    Output: alloy v0.1.0: Grafana Alloy for log collection... [#output-alloy-v010-grafana-alloy-for-log-collection]
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This property returns a new PluginMetadata instance on each access.
    The metadata is static and does not change at runtime.
  </Callout>
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load and parse the Alloy service definition from package resources.

  Reads the embedded `service.yaml` file from the package resources and
  parses it into a Python dictionary. This configuration defines the Docker
  Compose-style service specification for running Grafana Alloy, including
  container configuration, volume mounts, port mappings, and environment
  variables.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Load and inspect the service definition::

    plugin = AlloyServicePlugin()
    config = plugin.service\_definition
    image = config.get("image")
    ports = config.get("ports", \[])
    print(f"Alloy service image: \{image}")
    print(f"Exposed ports: \{ports}")
  </Callout>

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    The `service.yaml` file is embedded in the package at build time.
    Any changes to the file require reinstalling the package. The file
    is read on every access to this property, so consider caching if
    accessed frequently in a loop.
  </Callout>

  <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
    importlib.resources: Used for accessing package resources.
    yaml.safe\_load: Used for parsing YAML configuration safely.
  </Callout>
</PyAttribute>
