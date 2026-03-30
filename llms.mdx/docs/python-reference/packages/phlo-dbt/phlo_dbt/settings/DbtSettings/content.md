# DbtSettings (/docs/python-reference/packages/phlo-dbt/phlo_dbt/settings/DbtSettings)



dbt project configuration settings.

Pydantic-based configuration class that manages all dbt-related settings
including query engine connection parameters, project paths, and artifact
locations. Uses environment variables and .env files for configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;dbt_query_engine_type&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='trino', description='Query engine adapter used by dbt profiles')&#x22;">
  Query engine adapter type (default: "trino").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='trino', description='Query engine host for generated dbt profiles')&#x22;">
  Query engine hostname (default: "trino").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=8080, description='Query engine port for generated dbt profiles')&#x22;">
  Query engine port (default: 8080).
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='iceberg', description='Base query engine catalog for generated dbt profiles')&#x22;">
  Base catalog name (default: "iceberg").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_schema&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='raw', description='Default schema for generated dbt profiles')&#x22;">
  Default schema (default: "raw").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='dagster', description='Query engine user for generated dbt profiles')&#x22;">
  Database user (default: "dagster").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_http_scheme&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='http', description='HTTP scheme for generated dbt profiles')&#x22;">
  HTTP scheme (default: "http").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_auth_method&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='none', description='Auth method for generated dbt profiles')&#x22;">
  Auth method (default: "none").
</PyAttribute>

<PyAttribute name="&#x22;dbt_query_threads&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=2, description='Worker threads for generated dbt profiles')&#x22;">
  Parallel threads (default: 2).
</PyAttribute>

<PyAttribute name="&#x22;dbt_project_dir&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='workflows/transforms/dbt', description='Path to dbt project directory')&#x22;">
  Path to dbt project directory (default: "workflows/transforms/dbt").
</PyAttribute>

<PyAttribute name="&#x22;dbt_manifest_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='', description='Path to dbt manifest.json after running dbt docs generate')&#x22;">
  Path to manifest.json (auto-derived if empty).
</PyAttribute>

<PyAttribute name="&#x22;dbt_catalog_path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='', description='Path to dbt catalog.json for column-level documentation')&#x22;">
  Path to catalog.json (auto-derived if empty).
</PyAttribute>

<PyAttribute name="&#x22;dbt_profiles_dir&#x22;" type="&#x22;str&#x22;" value="null">
  Return the dbt profiles directory path string.
</PyAttribute>

<PyAttribute name="&#x22;dbt_project_path&#x22;" type="&#x22;Path&#x22;" value="null">
  Return the dbt project path as a `Path`.
</PyAttribute>

<PyAttribute name="&#x22;dbt_profiles_path&#x22;" type="&#x22;Path&#x22;" value="null">
  Return the dbt profiles path as a `Path`.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Populate derived dbt artifact paths after model initialization.

  <PySourceCode>
    ```python
    def model_post_init(self, __context: object) -> None:
        """Populate derived dbt artifact paths after model initialization.

        Args:
            __context: Pydantic post-init context.

        """
        if not self.dbt_manifest_path:
            object.__setattr__(
                self, "dbt_manifest_path", f"{self.dbt_project_dir}/target/manifest.json"
            )
        if not self.dbt_catalog_path:
            object.__setattr__(
                self, "dbt_catalog_path", f"{self.dbt_project_dir}/target/catalog.json"
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;object&#x22;" value="undefined">
      Pydantic post-init context.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
