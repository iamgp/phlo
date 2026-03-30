# MinioResourceProvider (/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioResourceProvider)



Resource provider plugin exposing MinIO object storage capabilities.

This plugin implements the ResourceProviderPlugin interface to
expose MinIO as an object storage capability within Phlo's
capability framework. It enables other Phlo components to
discover and use MinIO for S3-compatible storage operations.

The provider exposes:

* ObjectStoreSpec for S3 operations
* Metadata for capability discovery
* Connection parameters for client configuration

Attributes [#attributes]

<PyAttribute name="&#x22;metadata&#x22;" type="&#x22;PluginMetadata&#x22;" value="null">
  PluginMetadata with provider identification and tags.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_resources&#x22;" type="&#x22;(self) -> list[ResourceSpec]&#x22;">
  Return resource specifications exposed by this provider.

  Currently returns an empty list as MinIO does not expose
  traditional resources through this provider. Object storage
  is provided via get\_object\_stores().

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    This method is required by the ResourceProviderPlugin interface.
    Use get\_object\_stores() for MinIO storage capabilities.
  </Callout>

  <PySourceCode>
    ```python
    def get_resources(self) -> list[ResourceSpec]:
        """Return resource specifications exposed by this provider.

        Currently returns an empty list as MinIO does not expose
        traditional resources through this provider. Object storage
        is provided via get_object_stores().

        Returns:
            list[ResourceSpec]: Empty list (no resources exposed).

        Examples:
            Check resources:
                >>> provider = MinioResourceProvider()
                >>> resources = provider.get_resources()
                >>> len(resources)
                0

        Note:
            This method is required by the ResourceProviderPlugin interface.
            Use get_object_stores() for MinIO storage capabilities.

        """
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ResourceSpec]: Empty list (no resources exposed).
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_object_stores&#x22;" type="&#x22;(self) -> list[ObjectStoreSpec]&#x22;">
  Return object storage capability specifications.

  Returns a list of ObjectStoreSpec instances representing the
  MinIO object storage capability. Each spec includes the provider
  instance and metadata for capability discovery.

  <Callout title="&#x22;Implementation&#x22;" type="&#x22;implementation&#x22;">
    Creates ObjectStoreSpec with MinioObjectStoreProvider:
    provider = MinioObjectStoreProvider()
    return \[ObjectStoreSpec(
    name="minio",
    provider=provider,
    metadata=\{...}
    )]
  </Callout>

  <PySourceCode>
    ```python
    def get_object_stores(self) -> list[ObjectStoreSpec]:
        """Return object storage capability specifications.

        Returns a list of ObjectStoreSpec instances representing the
        MinIO object storage capability. Each spec includes the provider
        instance and metadata for capability discovery.

        Returns:
            list[ObjectStoreSpec]: List containing one ObjectStoreSpec
                for the MinIO instance with:
                - name: "minio"
                - provider: MinioObjectStoreProvider instance
                - metadata: Storage type, endpoint, and S3 configuration

        Examples:
            Get object stores:
                >>> provider = MinioResourceProvider()
                >>> stores = provider.get_object_stores()
                >>> len(stores)
                1
                >>> store = stores[0]
                >>> store.name
                'minio'

            Access store metadata:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> print(store.metadata['type'])
                's3'
                >>> print(store.metadata['storage_system'])
                's3'
                >>> print(store.metadata['endpoint'])
                'http://minio:10001'

            Use with S3 client:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> conn = store.provider.to_sling_connection()
                >>>
                >>> # Use with boto3
                >>> import boto3
                >>> s3 = boto3.client('s3', **conn)
                >>> buckets = s3.list_buckets()
                >>> print([b['Name'] for b in buckets['Buckets']])
                ['bronze', 'silver', 'gold']

            Use with Sling:
                >>> provider = MinioResourceProvider()
                >>> store = provider.get_object_stores()[0]
                >>> conn = store.provider.to_sling_connection()
                >>>
                >>> # Configure Sling replication
                >>> sling_replication = {
                ...     'source': conn,
                ...     'target': {'type': 'postgres', 'url': '...'},
                ...     'streams': {
                ...         's3://bronze/raw-data/*.csv': {
                ...             'mode': 'incremental',
                ...             'primary_key': ['id']
                ...         }
                ...     }
                ... }

        Implementation:
            Creates ObjectStoreSpec with MinioObjectStoreProvider:
                provider = MinioObjectStoreProvider()
                return [ObjectStoreSpec(
                    name="minio",
                    provider=provider,
                    metadata={...}
                )]

        """
        provider = MinioObjectStoreProvider()
        return [
            ObjectStoreSpec(
                name="minio",
                provider=provider,
                metadata={
                    "storage_system": "s3",
                    "type": "s3",
                    "endpoint": provider.to_sling_connection()["endpoint"],
                },
            )
        ]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    list\[ObjectStoreSpec]: List containing one ObjectStoreSpec
    for the MinIO instance with:

    * name: "minio"
    * provider: MinioObjectStoreProvider instance
    * metadata: Storage type, endpoint, and S3 configuration
  </PyFunctionReturn>
</PyFunction>
