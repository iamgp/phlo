# catalog_backend (/docs/python-reference/packages/phlo-nessie/phlo_nessie/catalog_backend)



Nessie-owned PyIceberg catalog helpers.

This module provides utilities for loading and configuring PyIceberg catalogs
backed by Nessie. It handles S3 configuration, warehouse paths, and reference
branch management.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_pyiceberg_catalog_config&#x22;" type="&#x22;(ref) -> dict[str, Any]&#x22;">
      Build PyIceberg catalog configuration for Nessie backend.

      Constructs the configuration dictionary required by PyIceberg to connect
      to Nessie REST catalog with S3/MinIO storage backend.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > config = \_pyiceberg\_catalog\_config("main")
        > > > config\['type']
        > > > 'rest'
      </Callout>

      <PySourceCode>
        ```python
        def _pyiceberg_catalog_config(ref: str) -> dict[str, Any]:
            """Build PyIceberg catalog configuration for Nessie backend.

            Constructs the configuration dictionary required by PyIceberg to connect
            to Nessie REST catalog with S3/MinIO storage backend.

            Args:
                ref: Nessie reference (branch/tag) to use as catalog prefix.

            Returns:
                dict[str, Any]: PyIceberg catalog configuration dictionary.

            Example:
                >>> config = _pyiceberg_catalog_config("main")
                >>> config['type']
                'rest'

            """
            settings = get_settings()
            return {
                "type": "rest",
                "uri": f"{settings.nessie_iceberg_rest_uri()}/{ref}",
                "warehouse": os.environ.get("ICEBERG_WAREHOUSE_PATH", "s3://lake/warehouse"),
                "s3.endpoint": os.environ.get("ICEBERG_S3_ENDPOINT")
                or os.environ.get("S3_ENDPOINT", "http://minio:10001"),
                "s3.access-key-id": os.environ.get("ICEBERG_S3_ACCESS_KEY", "minio"),
                "s3.secret-access-key": os.environ.get("ICEBERG_S3_SECRET_KEY", "minio123"),
                "s3.path-style-access": "true",
                "s3.region": os.environ.get("ICEBERG_S3_REGION", "us-east-1"),
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="undefined">
          Nessie reference (branch/tag) to use as catalog prefix.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, Any]: PyIceberg catalog configuration dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;load_pyiceberg_catalog&#x22;" type="&#x22;(ref='main')&#x22;">
      Load the PyIceberg catalog using Nessie-owned catalog settings.

      Returns a cached PyIceberg catalog instance configured to connect to
      the Nessie REST catalog for the specified reference. Uses LRU cache
      to avoid redundant catalog initialization.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > catalog = load\_pyiceberg\_catalog("main")
        > > > tables = catalog.list\_tables("raw")
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Maximum of 16 cached catalogs are retained. Least recently used
        entries are evicted when cache is full.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=16)
        def load_pyiceberg_catalog(ref: str = "main"):
            """Load the PyIceberg catalog using Nessie-owned catalog settings.

            Returns a cached PyIceberg catalog instance configured to connect to
            the Nessie REST catalog for the specified reference. Uses LRU cache
            to avoid redundant catalog initialization.

            Args:
                ref: Nessie reference (branch or tag) to use. Defaults to "main".

            Returns:
                Catalog: PyIceberg catalog instance for the specified reference.

            Raises:
                RuntimeError: If PyIceberg is not installed.

            Example:
                >>> catalog = load_pyiceberg_catalog("main")
                >>> tables = catalog.list_tables("raw")

            Note:
                Maximum of 16 cached catalogs are retained. Least recently used
                entries are evicted when cache is full.

            """
            try:
                from pyiceberg.catalog import load_catalog
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "Iceberg catalog support is not installed. Install `phlo-nessie[iceberg-cli]`."
                ) from exc

            logger.debug("nessie_pyiceberg_catalog_load_requested", ref=ref)
            return load_catalog(name=f"iceberg_{ref}", **_pyiceberg_catalog_config(ref))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
          Nessie reference (branch or tag) to use. Defaults to "main".
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        PyIceberg catalog instance for the specified reference.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
