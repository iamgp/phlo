# MinioServicePlugin (/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioServicePlugin)



Service plugin for deploying MinIO S3-compatible object storage.

This plugin provides the MinIO service definition for Docker Compose
deployment. It implements the ServicePlugin interface to integrate
MinIO into Phlo's service management system.

The MinIO service runs on two ports:

* API port (default 10001): S3-compatible API endpoint
* Console port (default 10002): Web-based management UI

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata with name, version, and service info.
</PyAttribute>

<PyAttribute name="&#x22;service_definition&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null">
  Load the MinIO service definition from package resources.

  <Callout title="&#x22;Structure&#x22;" type="&#x22;structure&#x22;">
    The returned dict typically contains:
    \{
    'services': \{
    'minio': \{
    'image': 'minio/minio:latest',
    'ports': \['10001:9000', '10002:9001'],
    'environment': \{...},
    'volumes': \[...],
    'command': \[...]
    }
    },
    'volumes': \{...}
    }
  </Callout>
</PyAttribute>
