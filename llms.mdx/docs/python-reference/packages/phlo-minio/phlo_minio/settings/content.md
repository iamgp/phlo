# settings (/docs/python-reference/packages/phlo-minio/phlo_minio/settings)



MinIO settings module for S3-compatible storage configuration.

This module provides configuration management for MinIO connections,
including host resolution, port configuration, and S3-compatible settings.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MinioSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-minio/phlo_minio/settings/MinioSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> MinioSettings&#x22;">
      Return a cached MinIO settings instance.

      Creates and caches a single MinioSettings instance to avoid
      repeated environment resolution and configuration loading.
      The cache ensures consistent settings across the application
      lifecycle.

      <Callout title="&#x22;Warning&#x22;" type="&#x22;warning&#x22;">
        Settings are cached for the process lifetime. To refresh
        settings, restart the application process.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> MinioSettings:
            """Return a cached MinIO settings instance.

            Creates and caches a single MinioSettings instance to avoid
            repeated environment resolution and configuration loading.
            The cache ensures consistent settings across the application
            lifecycle.

            Returns:
                MinioSettings: Cached settings instance.

            Examples:
                Singleton pattern:
                    >>> settings1 = get_settings()
                    >>> settings2 = get_settings()
                    >>> settings1 is settings2  # Same instance
                    True

                Accessing configuration:
                    >>> settings = get_settings()
                    >>> endpoint = settings.minio_endpoint()
                    >>> print(f"MinIO at {endpoint}")
                    MinIO at minio:10001

                Integration with S3 clients:
                    >>> settings = get_settings()
                    >>> s3_config = {
                    ...     'endpoint_url': f"http://{settings.minio_endpoint()}",
                    ...     'aws_access_key_id': settings.minio_root_user,
                    ...     'aws_secret_access_key': settings.minio_root_password,
                    ...     'region_name': settings.s3_region
                    ... }

            Warning:
                Settings are cached for the process lifetime. To refresh
                settings, restart the application process.

            """
            return MinioSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_minio.settings.MinioSettings&#x22;">
        Cached settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
