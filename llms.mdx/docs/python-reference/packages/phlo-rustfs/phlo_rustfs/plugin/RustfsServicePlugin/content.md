# RustfsServicePlugin (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/plugin/RustfsServicePlugin)



Service plugin for RustFS.

Implements the ServicePlugin interface to provide Docker Compose service
definitions for running RustFS S3-compatible object storage. This is the
main service that runs the RustFS container.

The service definition includes volume mounts, port mappings, and health
checks for the RustFS S3 API and web console.

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  Return metadata describing the RustFS service plugin.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the RustFS service definition.

  Returns the Docker Compose service definition for running the RustFS
  container, including API and console port mappings, volume mounts,
  and health check configuration.
</PyAttribute>
