# MetricsBackendSettings (/docs/python-reference/core/phlo/metrics/MetricsBackendSettings)



Backend connection settings for metrics collection.

Attributes [#attributes]

<PyAttribute name="&#x22;postgres_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='postgres', description='PostgreSQL host')&#x22;" />

<PyAttribute name="&#x22;postgres_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=5432, description='PostgreSQL port')&#x22;" />

<PyAttribute name="&#x22;postgres_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL username')&#x22;" />

<PyAttribute name="&#x22;postgres_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL password')&#x22;" />

<PyAttribute name="&#x22;postgres_db&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='phlo', description='PostgreSQL database name')&#x22;" />

<PyAttribute name="&#x22;nessie_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='nessie', description='Nessie host')&#x22;" />

<PyAttribute name="&#x22;nessie_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=19120, description='Nessie port')&#x22;" />

<PyAttribute name="&#x22;nessie_api_version&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='v1', description='Nessie API version')&#x22;" />

<PyAttribute name="&#x22;metrics_query_engine&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Optional query_engine capability name for table stats queries')&#x22;" />

<PyAttribute name="&#x22;metrics_query_catalog&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Catalog name used for query-engine table stats lookups')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        host, port = resolve_host(
            self.postgres_host, self.postgres_port, port_env_var="POSTGRES_PORT"
        )
        object.__setattr__(self, "postgres_host", host)
        object.__setattr__(self, "postgres_port", port)
        nhost, nport = resolve_host(self.nessie_host, self.nessie_port, port_env_var="NESSIE_PORT")
        object.__setattr__(self, "nessie_host", nhost)
        object.__setattr__(self, "nessie_port", nport)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;nessie_api_uri&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the versioned Nessie API URI.

  <PySourceCode>
    ```python
    def nessie_api_uri(self) -> str:
        """Return the versioned Nessie API URI."""
        return f"http://{self.nessie_host}:{self.nessie_port}/api/{self.nessie_api_version}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;" />
</PyFunction>
