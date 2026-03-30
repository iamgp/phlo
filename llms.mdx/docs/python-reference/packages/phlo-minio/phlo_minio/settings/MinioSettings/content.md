# MinioSettings (/docs/python-reference/packages/phlo-minio/phlo_minio/settings/MinioSettings)



Configuration class for MinIO S3-compatible storage.

Provides settings for MinIO connection including host, credentials,
ports, and S3 region configuration. Supports environment-based
host resolution for Docker Compose and local development.

Attributes [#attributes]

<PyAttribute name="&#x22;minio_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio', description='MinIO service hostname')&#x22;">
  MinIO service hostname (default: "minio").
</PyAttribute>

<PyAttribute name="&#x22;minio_root_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio', description='MinIO root username')&#x22;">
  Root username for MinIO authentication.
</PyAttribute>

<PyAttribute name="&#x22;minio_root_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio123', description='MinIO root password')&#x22;">
  Root password for MinIO authentication.
</PyAttribute>

<PyAttribute name="&#x22;minio_api_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10001, description='MinIO API port')&#x22;">
  Port for S3 API operations.
</PyAttribute>

<PyAttribute name="&#x22;minio_console_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10002, description='MinIO console port')&#x22;">
  Port for MinIO web console.
</PyAttribute>

<PyAttribute name="&#x22;s3_region&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='us-east-1', description='S3 region')&#x22;">
  AWS S3-compatible region identifier.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Resolve host and port from environment variables if available.

  Updates the minio\_host and minio\_api\_port attributes based on
  environment configuration. This enables Docker Compose service
  discovery and local development overrides.

  <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
    Uses phlo.config.network.resolve\_host for environment-based
    resolution. The port\_env\_var parameter enables port override
    via MINIO\_API\_PORT environment variable.
  </Callout>

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Resolve host and port from environment variables if available.

        Updates the minio_host and minio_api_port attributes based on
        environment configuration. This enables Docker Compose service
        discovery and local development overrides.

        Args:
            __context: Pydantic internal context (unused).

        Examples:
            Automatic host resolution:
                # With MINIO_HOST=localhost in environment
                >>> settings = MinioSettings()
                >>> settings.minio_host  # Resolved to 'localhost'
                'localhost'

        Note:
            Uses phlo.config.network.resolve_host for environment-based
            resolution. The port_env_var parameter enables port override
            via MINIO_API_PORT environment variable.

        """
        host, port = resolve_host(
            self.minio_host, self.minio_api_port, port_env_var="MINIO_API_PORT"
        )
        object.__setattr__(self, "minio_host", host)
        object.__setattr__(self, "minio_api_port", port)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Pydantic internal context (unused).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;minio_endpoint&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the MinIO API endpoint as host:port string.

  <Callout title="&#x22;Use Case&#x22;" type="&#x22;use-case&#x22;">
    Use this endpoint for S3 client configuration:

    > > > import boto3
    > > > s3 = boto3.client(
    > > > ...     's3',
    > > > ...     endpoint\_url=f"http\://\{settings.minio\_endpoint()}",
    > > > ...     aws\_access\_key\_id=settings.minio\_root\_user,
    > > > ...     aws\_secret\_access\_key=settings.minio\_root\_password
    > > > ... )
  </Callout>

  <PySourceCode>
    ```python
    def minio_endpoint(self) -> str:
        """Return the MinIO API endpoint as host:port string.

        Returns:
            str: Formatted endpoint string (e.g., "minio:10001").

        Examples:
            Default endpoint:
                >>> settings = MinioSettings()
                >>> settings.minio_endpoint()
                'minio:10001'

            Custom endpoint:
                >>> settings = MinioSettings(minio_host="localhost", minio_api_port=9000)
                >>> settings.minio_endpoint()
                'localhost:9000'

        Use Case:
            Use this endpoint for S3 client configuration:
                >>> import boto3
                >>> s3 = boto3.client(
                ...     's3',
                ...     endpoint_url=f"http://{settings.minio_endpoint()}",
                ...     aws_access_key_id=settings.minio_root_user,
                ...     aws_secret_access_key=settings.minio_root_password
                ... )

        """
        return f"{self.minio_host}:{self.minio_api_port}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted endpoint string (e.g., "minio:10001").
  </PyFunctionReturn>
</PyFunction>
