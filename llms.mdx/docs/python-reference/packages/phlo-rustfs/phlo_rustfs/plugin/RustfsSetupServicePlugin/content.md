# RustfsSetupServicePlugin (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsSetupServicePlugin)



Service plugin for RustFS bucket initialization.

Implements the ServicePlugin interface to provide a Docker Compose service
definition for initializing RustFS buckets on startup. This service runs
once after the main RustFS container is healthy to create the default
buckets required by the data platform.

Depends on the main rustfs service and uses the MinIO client to create
buckets with appropriate access policies.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return metadata describing the RustFS setup plugin.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the RustFS setup service definition.

  Returns the Docker Compose service definition for the bucket
  initialization container. This service depends on the main rustfs
  service being healthy and runs the MinIO client to create buckets.
</PyAttribute>
