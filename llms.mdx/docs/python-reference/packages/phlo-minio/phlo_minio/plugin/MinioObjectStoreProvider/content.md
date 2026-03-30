# MinioObjectStoreProvider (/docs/python-reference/packages/phlo-minio/phlo_minio/plugin/MinioObjectStoreProvider)



Capability provider for MinIO-backed S3-compatible object storage.

This class provides object storage capabilities compatible with
S3 SDKs and tools. It handles configuration translation between
Phlo settings and various S3 client formats.

The provider supports:

* S3 API operations (boto3, aws-sdk, etc.)
* Sling replication tool integration
* Standard S3 endpoint configuration

Functions [#functions]

<PyFunction name="&#x22;to_sling_connection&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return a Sling-compatible S3 connection definition.

  Generates a connection dictionary compatible with the Sling
  data replication tool and similar S3-based systems.

  <Callout title="&#x22;Implementation&#x22;" type="&#x22;implementation&#x22;">
    Loads settings via get\_settings() and constructs endpoint:
    endpoint = f"http\://\{settings.minio\_endpoint()}"
  </Callout>

  <PySourceCode>
    ```python
    def to_sling_connection(self) -> dict[str, Any]:
        """Return a Sling-compatible S3 connection definition.

        Generates a connection dictionary compatible with the Sling
        data replication tool and similar S3-based systems.

        Returns:
            dict[str, Any]: Connection configuration with:
                - type: Always "s3"
                - endpoint: Full HTTP endpoint URL
                - access_key_id: MinIO root user
                - secret_access_key: MinIO root password
                - region: S3 region identifier

        Examples:
            Sling connection:
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> print(conn)
                {
                    'type': 's3',
                    'endpoint': 'http://minio:10001',
                    'access_key_id': 'minio',
                    'secret_access_key': 'minio123',
                    'region': 'us-east-1'
                }

            Sling replication config:
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> sling_config = {
                ...     'source': conn,
                ...     'target': {'type': 'postgres', ...},
                ...     'streams': {'s3://bucket/key': {'mode': 'full_refresh'}}
                ... }

            Direct S3 operations:
                >>> import boto3
                >>> provider = MinioObjectStoreProvider()
                >>> conn = provider.to_sling_connection()
                >>> s3 = boto3.client(
                ...     's3',
                ...     endpoint_url=conn['endpoint'],
                ...     aws_access_key_id=conn['access_key_id'],
                ...     aws_secret_access_key=conn['secret_access_key'],
                ...     region_name=conn['region']
                ... )
                >>> # Upload a file
                >>> s3.upload_file('data.csv', 'my-bucket', 'data.csv')
                >>> # Download a file
                >>> s3.download_file('my-bucket', 'data.csv', 'downloaded.csv')
                >>> # List objects
                >>> response = s3.list_objects_v2(Bucket='my-bucket', Prefix='data/')
                >>> print([obj['Key'] for obj in response.get('Contents', [])])

        Implementation:
            Loads settings via get_settings() and constructs endpoint:
                endpoint = f"http://{settings.minio_endpoint()}"

        """
        from phlo_minio.settings import get_settings

        settings = get_settings()
        return {
            "type": "s3",
            "endpoint": f"http://{settings.minio_endpoint()}",
            "access_key_id": settings.minio_root_user,
            "secret_access_key": settings.minio_root_password,
            "region": settings.s3_region,
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, Any]: Connection configuration with:

    * type: Always "s3"
    * endpoint: Full HTTP endpoint URL
    * access\_key\_id: MinIO root user
    * secret\_access\_key: MinIO root password
    * region: S3 region identifier
  </PyFunctionReturn>
</PyFunction>
