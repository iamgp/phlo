# DeltaSettings (/docs/python-reference/packages/phlo-delta/phlo_delta/settings/DeltaSettings)



Delta Lake storage configuration.

This class manages all configuration settings for Delta Lake operations,
including S3 storage paths, endpoints, credentials, and behavior flags.

Attributes [#attributes]

<PyAttribute name="&#x22;delta_warehouse_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='s3://lake/warehouse/delta', description='S3 path for Delta tables')&#x22;">
  S3 URI path for Delta table storage.
</PyAttribute>

<PyAttribute name="&#x22;delta_staging_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='s3://lake/stage', description='S3 path for staging parquet files')&#x22;">
  S3 URI path for staging parquet files.
</PyAttribute>

<PyAttribute name="&#x22;delta_default_namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='raw', description='Default namespace/schema for Delta tables')&#x22;">
  Default database/schema namespace for tables.
</PyAttribute>

<PyAttribute name="&#x22;delta_s3_endpoint&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default='http://localhost:9000', validation_alias=(AliasChoices('DELTA_S3_ENDPOINT', 'AWS_S3_ENDPOINT')), description='S3 endpoint URL for Delta I/O')&#x22;">
  S3-compatible endpoint URL for Delta I/O operations.
</PyAttribute>

<PyAttribute name="&#x22;delta_s3_access_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio', validation_alias=(AliasChoices('DELTA_S3_ACCESS_KEY', 'AWS_ACCESS_KEY_ID')), description='S3 access key for Delta I/O')&#x22;">
  Access key for S3 authentication.
</PyAttribute>

<PyAttribute name="&#x22;delta_s3_secret_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio123', validation_alias=(AliasChoices('DELTA_S3_SECRET_KEY', 'AWS_SECRET_ACCESS_KEY')), description='S3 secret key for Delta I/O')&#x22;">
  Secret key for S3 authentication.
</PyAttribute>

<PyAttribute name="&#x22;delta_s3_region&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='us-east-1', validation_alias=(AliasChoices('DELTA_S3_REGION', 'AWS_REGION')), description='S3 region for Delta I/O')&#x22;">
  AWS region for S3 operations.
</PyAttribute>

<PyAttribute name="&#x22;delta_s3_allow_unsafe_rename&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Allow unsafe rename for S3 (non-HDFS) backends')&#x22;">
  Flag to allow unsafe renames on S3 backends.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Post-initialization hook to resolve S3 endpoint URL.

  Resolves the delta\_s3\_endpoint using the network URL resolver,
  handling port environment variable substitution.

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to resolve S3 endpoint URL.

        Resolves the delta_s3_endpoint using the network URL resolver,
        handling port environment variable substitution.

        Args:
            __context: Pydantic initialization context.

        """
        if self.delta_s3_endpoint:
            resolved = resolve_url(self.delta_s3_endpoint, port_env_var="MINIO_API_PORT")
            object.__setattr__(self, "delta_s3_endpoint", resolved)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Pydantic initialization context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_storage_options&#x22;" type="&#x22;(self) -> dict[str, str]&#x22;">
  Build deltalake storage options dict for S3 access.

  Constructs a dictionary of storage options compatible with the
  deltalake library's S3 I/O operations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    settings = DeltaSettings()
    opts = settings.get\_storage\_options()

    Returns: {"AWS_ACCESS_KEY_ID": "...", ...} [#returns-aws_access_key_id--]
  </Callout>

  <PySourceCode>
    ```python
    def get_storage_options(self) -> dict[str, str]:
        """Build deltalake storage options dict for S3 access.

        Constructs a dictionary of storage options compatible with the
        deltalake library's S3 I/O operations.

        Returns:
            dict[str, str]: Storage options containing AWS credentials,
                endpoint URL, region, and safety flags.

        Example:
            settings = DeltaSettings()
            opts = settings.get_storage_options()
            # Returns: {"AWS_ACCESS_KEY_ID": "...", ...}

        """
        opts: dict[str, str] = {
            "AWS_ACCESS_KEY_ID": self.delta_s3_access_key,
            "AWS_SECRET_ACCESS_KEY": self.delta_s3_secret_key,
            "AWS_REGION": self.delta_s3_region,
            "AWS_ALLOW_HTTP": "true",
        }
        if self.delta_s3_endpoint:
            opts["AWS_ENDPOINT_URL"] = self.delta_s3_endpoint
        if self.delta_s3_allow_unsafe_rename:
            opts["AWS_S3_ALLOW_UNSAFE_RENAME"] = "true"
        return opts
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    dict\[str, str]: Storage options containing AWS credentials,
    endpoint URL, region, and safety flags.
  </PyFunctionReturn>
</PyFunction>
