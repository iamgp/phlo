# MinioSetupServicePlugin (/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioSetupServicePlugin)



Service plugin for MinIO bucket initialization.

This plugin provides a one-time setup service that creates default
buckets in MinIO during the initial deployment. It runs as a
separate container that executes bucket creation commands and exits.

The setup service:

* Creates default buckets (bronze, silver, gold for medallion architecture)
* Sets bucket policies and lifecycle rules
* Runs once during 'phlo services start' or on demand
* Exits cleanly after completion

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata with setup service information.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the MinIO setup service definition from package resources.

  <Callout title="&#x22;Structure&#x22;" type="&#x22;structure&#x22;">
    The setup service typically:

    * Depends on minio service being healthy
    * Uses mc (MinIO Client) to create buckets
    * Has restart policy set to 'no'
    * Exits after creating configured buckets
  </Callout>
</PyAttribute>
