# trino (/docs/python-reference/packages/phlo-nessie/phlo_nessie/adapters/trino)



Trino catalog plugins for Nessie-backed Iceberg catalogs.

This module provides Trino catalog plugins that configure Iceberg connections
backed by Nessie's REST catalog API. Supports both production and development
Nessie references.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;TrinoNessieIcebergCatalogPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-nessie/phlo_nessie/adapters/trino/TrinoNessieIcebergCatalogPlugin&#x22;" />

      <Card title="&#x22;TrinoNessieIcebergDevCatalogPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-nessie/phlo_nessie/adapters/trino/TrinoNessieIcebergDevCatalogPlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_nessie_iceberg_rest_uri&#x22;" type="&#x22;() -> str&#x22;">
      Build the Nessie Iceberg REST URI from environment settings.

      Constructs the URI using NESSIE\_HOST and NESSIE\_PORT environment variables,
      with sensible defaults if not set.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > uri = \_nessie\_iceberg\_rest\_uri()
        > > > '[http://nessie:19120/iceberg](http://nessie:19120/iceberg)'
      </Callout>

      <PySourceCode>
        ```python
        def _nessie_iceberg_rest_uri() -> str:
            """Build the Nessie Iceberg REST URI from environment settings.

            Constructs the URI using NESSIE_HOST and NESSIE_PORT environment variables,
            with sensible defaults if not set.

            Returns:
                str: Full Nessie Iceberg REST catalog URI.

            Example:
                >>> uri = _nessie_iceberg_rest_uri()
                'http://nessie:19120/iceberg'

            """
            host = os.environ.get("NESSIE_HOST", "nessie")
            port = os.environ.get("NESSIE_PORT", "19120")
            return f"http://{host}:{port}/iceberg"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Full Nessie Iceberg REST catalog URI.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_base_iceberg_catalog_properties&#x22;" type="&#x22;(*, prefix=None) -> dict[str, str]&#x22;">
      Build shared Trino Iceberg catalog properties for a Nessie backend.

      Configures Trino connector properties for Iceberg REST catalog backed by
      Nessie. Includes S3/MinIO configuration for warehouse storage.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > props = \_base\_iceberg\_catalog\_properties()
        > > > props\['iceberg.catalog.type']
        > > > 'rest'
      </Callout>

      <PySourceCode>
        ```python
        def _base_iceberg_catalog_properties(*, prefix: str | None = None) -> dict[str, str]:
            """Build shared Trino Iceberg catalog properties for a Nessie backend.

            Configures Trino connector properties for Iceberg REST catalog backed by
            Nessie. Includes S3/MinIO configuration for warehouse storage.

            Args:
                prefix: Optional catalog prefix for namespacing (e.g., 'dev' for dev branch).

            Returns:
                dict[str, str]: Trino catalog configuration properties.

            Example:
                >>> props = _base_iceberg_catalog_properties()
                >>> props['iceberg.catalog.type']
                'rest'

            """
            minio_endpoint = os.environ.get("S3_ENDPOINT", "http://minio:9000")
            s3_region = os.environ.get("AWS_REGION", "us-east-1")

            props: dict[str, str] = {
                "connector.name": "iceberg",
                "iceberg.catalog.type": "rest",
                "iceberg.rest-catalog.uri": _nessie_iceberg_rest_uri(),
                "iceberg.rest-catalog.warehouse": "warehouse",
                "fs.native-s3.enabled": "true",
                "s3.endpoint": minio_endpoint,
                "s3.path-style-access": "true",
                "s3.region": s3_region,
            }
            if prefix is not None:
                props["iceberg.rest-catalog.prefix"] = prefix
            return props
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;prefix&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional catalog prefix for namespacing (e.g., 'dev' for dev branch).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, str]: Trino catalog configuration properties.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
