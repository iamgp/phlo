# DbtRuntimeConfig (/docs/python-reference/packages/phlo-dbt/phlo_dbt/runtime_config/DbtRuntimeConfig)



Canonical dbt runtime configuration for the active execution target.

This dataclass holds all configuration needed to generate a dbt profile,
including connection details for the query engine (typically Trino),
authentication settings, and execution parameters.

Attributes [#attributes]

<PyAttribute name="&#x22;profile_name&#x22;" type="&#x22;str&#x22;" value="&#x22;DEFAULT_DBT_PROFILE_NAME&#x22;">
  Name of the dbt profile (default: "phlo").
</PyAttribute>

<PyAttribute name="&#x22;target_name&#x22;" type="&#x22;str&#x22;" value="&#x22;DEFAULT_DBT_TARGET&#x22;">
  dbt target environment name (default: "dev").
</PyAttribute>

<PyAttribute name="&#x22;engine_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'trino'&#x22;">
  Query engine adapter type (default: "trino").
</PyAttribute>

<PyAttribute name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'dagster'&#x22;">
  Database user for connections (default: "dagster").
</PyAttribute>

<PyAttribute name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="&#x22;'trino'&#x22;">
  Query engine hostname (default: "trino").
</PyAttribute>

<PyAttribute name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="&#x22;8080&#x22;">
  Query engine port (default: 8080).
</PyAttribute>

<PyAttribute name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;'iceberg'&#x22;">
  Default catalog name (default: "iceberg").
</PyAttribute>

<PyAttribute name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'raw'&#x22;">
  Default schema name (default: "raw").
</PyAttribute>

<PyAttribute name="&#x22;threads&#x22;" type="&#x22;int&#x22;" value="&#x22;2&#x22;">
  Number of parallel threads for dbt execution (default: 2).
</PyAttribute>

<PyAttribute name="&#x22;http_scheme&#x22;" type="&#x22;str&#x22;" value="&#x22;'http'&#x22;">
  HTTP scheme for connections (default: "http").
</PyAttribute>

<PyAttribute name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="&#x22;'none'&#x22;">
  Authentication method (default: "none").
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;to_profile_payload&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Return the config in dbt `profiles.yml` shape.

  Converts this configuration into the YAML structure expected by dbt,
  including the profile name, target, and output configuration.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > config = DbtRuntimeConfig(target\_name="prod")
    > > > payload = config.to\_profile\_payload()
    > > > "phlo" in payload
    > > > True
  </Callout>

  <PySourceCode>
    ```python
    def to_profile_payload(self) -> dict[str, Any]:
        """Return the config in dbt `profiles.yml` shape.

        Converts this configuration into the YAML structure expected by dbt,
        including the profile name, target, and output configuration.

        Returns:
            Dictionary formatted as dbt profiles.yml content.

        Example:
            >>> config = DbtRuntimeConfig(target_name="prod")
            >>> payload = config.to_profile_payload()
            >>> "phlo" in payload
            True

        """
        return {
            self.profile_name: {
                "target": self.target_name,
                "outputs": {
                    self.target_name: {
                        "type": self.engine_type,
                        "method": self.method,
                        "user": self.user,
                        "host": self.host,
                        "port": self.port,
                        "catalog": self.catalog,
                        "schema": self.schema,
                        "http_scheme": self.http_scheme,
                        "threads": self.threads,
                    }
                },
            }
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary formatted as dbt profiles.yml content.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, profile_name=DEFAULT_DBT_PROFILE_NAME, target_name=DEFAULT_DBT_TARGET, engine_type='trino', user='dagster', host='trino', port=8080, catalog='iceberg', schema='raw', threads=2, http_scheme='http', method='none') -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;profile_name&#x22;" type="&#x22;str&#x22;" value="&#x22;DEFAULT_DBT_PROFILE_NAME&#x22;" />

    <PyParameter name="&#x22;target_name&#x22;" type="&#x22;str&#x22;" value="&#x22;DEFAULT_DBT_TARGET&#x22;" />

    <PyParameter name="&#x22;engine_type&#x22;" type="&#x22;str&#x22;" value="&#x22;'trino'&#x22;" />

    <PyParameter name="&#x22;user&#x22;" type="&#x22;str&#x22;" value="&#x22;'dagster'&#x22;" />

    <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="&#x22;'trino'&#x22;" />

    <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="&#x22;8080&#x22;" />

    <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;'iceberg'&#x22;" />

    <PyParameter name="&#x22;schema&#x22;" type="&#x22;str&#x22;" value="&#x22;'raw'&#x22;" />

    <PyParameter name="&#x22;threads&#x22;" type="&#x22;int&#x22;" value="&#x22;2&#x22;" />

    <PyParameter name="&#x22;http_scheme&#x22;" type="&#x22;str&#x22;" value="&#x22;'http'&#x22;" />

    <PyParameter name="&#x22;method&#x22;" type="&#x22;str&#x22;" value="&#x22;'none'&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
