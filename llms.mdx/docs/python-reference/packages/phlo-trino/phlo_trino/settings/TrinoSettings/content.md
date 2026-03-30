# TrinoSettings (/docs/python-reference/packages/phlo-trino/phlo_trino/settings/TrinoSettings)



Trino query engine configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;trino_version&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='477', description='Trino version')&#x22;" />

<PyAttribute name="&#x22;trino_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=10005, description='Trino HTTP port')&#x22;" />

<PyAttribute name="&#x22;trino_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='trino', description='Trino service hostname')&#x22;" />

<PyAttribute name="&#x22;trino_catalog&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='iceberg', description='Trino catalog name for Iceberg')&#x22;" />

<PyAttribute name="&#x22;trino_default_ref&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='main', description='Default branch/tag suffix')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Post-initialization hook to resolve host and port.

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to resolve host and port."""
        host, port = resolve_host(self.trino_host, self.trino_port, port_env_var="TRINO_PORT")
        object.__setattr__(self, "trino_host", host)
        object.__setattr__(self, "trino_port", port)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;trino_connection_string&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the Trino DSN for current settings.

  <PySourceCode>
    ```python
    def trino_connection_string(self) -> str:
        """Return the Trino DSN for current settings.

        Returns:
            DSN string derived from configured host, port, and catalog.

        """
        return build_trino_dsn(self.trino_host, self.trino_port, self.trino_catalog)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    DSN string derived from configured host, port, and catalog.
  </PyFunctionReturn>
</PyFunction>
