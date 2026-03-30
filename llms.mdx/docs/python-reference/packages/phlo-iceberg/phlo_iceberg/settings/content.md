# settings (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/settings)



Iceberg settings configuration.

This module provides configuration management for Iceberg connections,
including warehouse paths, S3 storage settings, and Nessie catalog endpoints.

Settings are loaded from environment variables and `.phlo/.env` files,
following Phlo's standard configuration pattern.

Configuration precedence:

1. Environment variables (`PHLO_ICEBERG_*`)
2. `.phlo/.env.local` (local overrides)
3. `.phlo/.env` (project defaults)
4. Default values defined in this module

Example:
Basic settings usage::

from phlo\_iceberg.settings import get\_settings

settings = get\_settings()
print(f"Warehouse: \{settings.iceberg\_warehouse\_path}")
print(f"Default branch: \{settings.iceberg\_default\_ref}")

Get catalog config for PyIceberg [#get-catalog-config-for-pyiceberg]

catalog\_config = settings.get\_pyiceberg\_catalog\_config(ref="main")

Environment variables::

export PHLO\_ICEBERG\_WAREHOUSE\_PATH=s3://my-bucket/warehouse
export PHLO\_ICEBERG\_DEFAULT\_REF=main
export PHLO\_ICEBERG\_S3\_ACCESS\_KEY=mykey
export PHLO\_ICEBERG\_S3\_SECRET\_KEY=mysecret

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IcebergSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/settings/IcebergSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> IcebergSettings&#x22;">
      Get cached Iceberg settings instance.

      Uses LRU cache to avoid repeatedly loading and parsing configuration.
      The cache has size 1, meaning only one settings instance is kept.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Get settings::

        from phlo\_iceberg.settings import get\_settings

        settings = get\_settings()
        print(f"Warehouse: \{settings.iceberg\_warehouse\_path}")
        print(f"Default namespace: \{settings.iceberg\_default\_namespace}")
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Settings are cached. To force reload after configuration changes,
        restart the Python process or clear the cache with::

        get\_settings.cache\_clear()
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> IcebergSettings:
            """Get cached Iceberg settings instance.

            Uses LRU cache to avoid repeatedly loading and parsing configuration.
            The cache has size 1, meaning only one settings instance is kept.

            Returns:
                IcebergSettings: Cached Iceberg settings instance with all
                    configuration values resolved from environment and files.

            Example:
                Get settings::

                    from phlo_iceberg.settings import get_settings

                    settings = get_settings()
                    print(f"Warehouse: {settings.iceberg_warehouse_path}")
                    print(f"Default namespace: {settings.iceberg_default_namespace}")

            Note:
                Settings are cached. To force reload after configuration changes,
                restart the Python process or clear the cache with::

                    get_settings.cache_clear()

            """
            return IcebergSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_iceberg.settings.IcebergSettings&#x22;">
        Cached Iceberg settings instance with all
        configuration values resolved from environment and files.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
