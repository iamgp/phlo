# IcebergSettings (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/settings/IcebergSettings)



Iceberg catalog and storage configuration.

Defines all configuration parameters for connecting to Iceberg via
Nessie REST catalog and S3-compatible storage (MinIO).

Attributes [#attributes]

<PyAttribute name="&#x22;iceberg_warehouse_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='s3://lake/warehouse', description='S3 path for Iceberg warehouse')&#x22;">
  S3 path for the Iceberg warehouse.
  Default: `s3://lake/warehouse`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_staging_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='s3://lake/stage', description='S3 path for staging parquet files')&#x22;">
  S3 path for staging Parquet files.
  Default: `s3://lake/stage`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_default_namespace&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='raw', description='Default namespace/schema for Iceberg tables')&#x22;">
  Default namespace for new tables.
  Default: `raw`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_default_ref&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='main', description='Default catalog ref/branch for Iceberg operations')&#x22;">
  Default Nessie branch/tag reference.
  Default: `main`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_s3_endpoint&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default='http://minio:10001', description='S3 endpoint URL for Iceberg I/O')&#x22;">
  S3-compatible endpoint URL (MinIO).
  Default: `http://minio:10001`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_s3_access_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio', description='S3 access key for Iceberg I/O')&#x22;">
  S3 access key for storage operations.
  Default: `minio`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_s3_secret_key&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='minio123', description='S3 secret key for Iceberg I/O')&#x22;">
  S3 secret key for storage operations.
  Default: `minio123`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_s3_region&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='us-east-1', description='S3 region for Iceberg I/O')&#x22;">
  AWS-style region for S3 operations.
  Default: `us-east-1`.
</PyAttribute>

<PyAttribute name="&#x22;iceberg_catalog_uri&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='http://nessie:19120/iceberg', description='Iceberg REST catalog endpoint base URI')&#x22;">
  Nessie REST catalog endpoint base URI.
  Default: `http://nessie:19120/iceberg`.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;get_iceberg_warehouse_for_branch&#x22;" type="&#x22;(self, branch='main') -> str&#x22;">
  Get the warehouse path for a specific branch.

  Currently returns the same warehouse path for all branches.
  Future versions may support branch-specific warehouse locations.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Get warehouse path::

    settings = get\_settings()
    path = settings.get\_iceberg\_warehouse\_for\_branch("main")
    print(f"Warehouse: \{path}")  # s3://lake/warehouse
  </Callout>

  <PySourceCode>
    ```python
    def get_iceberg_warehouse_for_branch(self, branch: str = "main") -> str:
        """Get the warehouse path for a specific branch.

        Currently returns the same warehouse path for all branches.
        Future versions may support branch-specific warehouse locations.

        Args:
            branch: Nessie branch name.

        Returns:
            str: Warehouse path for the requested branch.

        Example:
            Get warehouse path::

                settings = get_settings()
                path = settings.get_iceberg_warehouse_for_branch("main")
                print(f"Warehouse: {path}")  # s3://lake/warehouse

        """
        return self.iceberg_warehouse_path
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;branch&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
      Nessie branch name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Warehouse path for the requested branch.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_pyiceberg_catalog_config&#x22;" type="&#x22;(self, ref='main') -> dict&#x22;">
  Build PyIceberg REST catalog configuration dictionary.

  Constructs a configuration dict suitable for passing to
  `pyiceberg.catalog.load_catalog()`. Resolves service URLs
  dynamically based on environment configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    Configure PyIceberg catalog::

    from pyiceberg.catalog import load\_catalog
    from phlo\_iceberg.settings import get\_settings

    settings = get\_settings()
    config = settings.get\_pyiceberg\_catalog\_config(ref="dev")
    catalog = load\_catalog("dev\_catalog", \*\*config)

    Now use catalog [#now-use-catalog]

    tables = catalog.list\_tables("raw")
  </Callout>

  <PySourceCode>
    ```python
    def get_pyiceberg_catalog_config(self, ref: str = "main") -> dict:
        """Build PyIceberg REST catalog configuration dictionary.

        Constructs a configuration dict suitable for passing to
        ``pyiceberg.catalog.load_catalog()``. Resolves service URLs
        dynamically based on environment configuration.

        Args:
            ref: Nessie reference (branch or tag) to target.

        Returns:
            dict: PyIceberg catalog configuration with keys:
                - ``type``: Always "rest"
                - ``uri``: Full catalog URI including ref path
                - ``warehouse``: Warehouse path
                - ``s3.endpoint``: S3 endpoint URL
                - ``s3.access-key-id``: S3 access key
                - ``s3.secret-access-key``: S3 secret key
                - ``s3.path-style-access``: Always "true" (MinIO compatibility)
                - ``s3.region``: S3 region

        Example:
            Configure PyIceberg catalog::

                from pyiceberg.catalog import load_catalog
                from phlo_iceberg.settings import get_settings

                settings = get_settings()
                config = settings.get_pyiceberg_catalog_config(ref="dev")
                catalog = load_catalog("dev_catalog", **config)

                # Now use catalog
                tables = catalog.list_tables("raw")

        """
        catalog_uri = _resolve_service_url(self.iceberg_catalog_uri, port_env_var="NESSIE_PORT")
        s3_endpoint = _resolve_service_url(self.iceberg_s3_endpoint, port_env_var="MINIO_API_PORT")
        return {
            "type": "rest",
            "uri": f"{catalog_uri}/{ref}",
            "warehouse": self.get_iceberg_warehouse_for_branch(ref),
            "s3.endpoint": s3_endpoint,
            "s3.access-key-id": self.iceberg_s3_access_key,
            "s3.secret-access-key": self.iceberg_s3_secret_key,
            "s3.path-style-access": "true",
            "s3.region": self.iceberg_s3_region,
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="&#x22;'main'&#x22;">
      Nessie reference (branch or tag) to target.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    PyIceberg catalog configuration with keys:

    * `type`: Always "rest"
    * `uri`: Full catalog URI including ref path
    * `warehouse`: Warehouse path
    * `s3.endpoint`: S3 endpoint URL
    * `s3.access-key-id`: S3 access key
    * `s3.secret-access-key`: S3 secret key
    * `s3.path-style-access`: Always "true" (MinIO compatibility)
    * `s3.region`: S3 region
  </PyFunctionReturn>
</PyFunction>
