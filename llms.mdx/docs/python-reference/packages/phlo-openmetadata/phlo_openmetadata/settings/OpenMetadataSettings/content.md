# OpenMetadataSettings (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/settings/OpenMetadataSettings)



OpenMetadata integration configuration.

Manages all configuration settings for OpenMetadata integration including
connection parameters, authentication credentials, and sync behavior.

Attributes [#attributes]

<PyAttribute name="&#x22;openmetadata_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='openmetadata-server', description='OpenMetadata server hostname')&#x22;">
  Server hostname.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=8585, description='OpenMetadata server port')&#x22;">
  Server port.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_username&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='admin', description='OpenMetadata admin username')&#x22;">
  Authentication username.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='admin', description='OpenMetadata admin password')&#x22;">
  Authentication password.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_verify_ssl&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=False, description='Verify SSL certificates for OpenMetadata connections')&#x22;">
  SSL certificate verification flag.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_service_name&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='OpenMetadata database service name for Phlo metadata sync')&#x22;">
  Database service name.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_service_type&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='OpenMetadata database service type (required unless query_engine metadata declares service_type)')&#x22;">
  Database service type.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_catalog_scanner&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Catalog scanner capability name to use for sync operations')&#x22;">
  Catalog scanner capability name.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_query_engine&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Query engine capability name used to infer the OpenMetadata database name')&#x22;">
  Query engine capability name.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_database_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='OpenMetadata database name (required unless a query_engine capability declares catalog metadata)')&#x22;">
  Explicit database name.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_dbt_manifest_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='workflows/transforms/dbt/target/manifest.json', description='Path to dbt manifest.json for metadata sync')&#x22;">
  Path to dbt manifest.json.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_dbt_catalog_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='workflows/transforms/dbt/target/catalog.json', description='Path to dbt catalog.json for metadata sync')&#x22;">
  Path to dbt catalog.json.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_sync_enabled&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=True, description='Enable automatic metadata sync to OpenMetadata')&#x22;">
  Enable automatic sync flag.
</PyAttribute>

<PyAttribute name="&#x22;openmetadata_sync_interval_seconds&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=300, description='Minimum interval between metadata syncs (seconds)')&#x22;">
  Minimum sync interval.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;openmetadata_uri&#x22;" type="&#x22;(self) -> str&#x22;">
  Build the OpenMetadata API base URI.

  <PySourceCode>
    ```python
    def openmetadata_uri(self) -> str:
        """Build the OpenMetadata API base URI.

        Returns:
            str: Base API URI for OpenMetadata.

        """
        return f"http://{self.openmetadata_host}:{self.openmetadata_port}/api"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Base API URI for OpenMetadata.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;openmetadata_database&#x22;" type="&#x22;(self) -> str&#x22;">
  Resolve the OpenMetadata database name.

  Uses explicit configuration or discovers from query engine capability.

  <PySourceCode>
    ```python
    def openmetadata_database(self) -> str:
        """Resolve the OpenMetadata database name.

        Uses explicit configuration or discovers from query engine capability.

        Returns:
            str: Explicit OpenMetadata database name or discovered query-engine catalog.

        Raises:
            RuntimeError: If database name cannot be resolved from configuration
                or query engine metadata.

        """
        if self.openmetadata_database_name:
            return self.openmetadata_database_name
        return resolve_query_engine_catalog(self.openmetadata_query_engine)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Explicit OpenMetadata database name or discovered query-engine catalog.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;openmetadata_database_service_type&#x22;" type="&#x22;(self) -> str&#x22;">
  Resolve the OpenMetadata service type.

  Uses explicit configuration or discovers from query engine capability.

  <PySourceCode>
    ```python
    def openmetadata_database_service_type(self) -> str:
        """Resolve the OpenMetadata service type.

        Uses explicit configuration or discovers from query engine capability.

        Returns:
            str: Service type for OpenMetadata (e.g., 'Trino', 'Snowflake').

        Raises:
            RuntimeError: If service type cannot be resolved from configuration
                or query engine metadata.

        """
        if self.openmetadata_service_type:
            return self.openmetadata_service_type
        return resolve_query_engine_service_type(self.openmetadata_query_engine)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Service type for OpenMetadata (e.g., 'Trino', 'Snowflake').
  </PyFunctionReturn>
</PyFunction>
