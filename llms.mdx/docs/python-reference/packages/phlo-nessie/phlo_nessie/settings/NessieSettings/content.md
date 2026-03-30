# NessieSettings (/docs/python-reference/packages/phlo-nessie/phlo_nessie/settings/NessieSettings)



Nessie catalog configuration.

Attributes [#attributes]

<PyAttribute name="&#x22;nessie_version&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='0.107.2', description='Nessie version')&#x22;" />

<PyAttribute name="&#x22;nessie_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=19120, description='Nessie REST API port')&#x22;" />

<PyAttribute name="&#x22;nessie_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='nessie', description='Nessie service hostname')&#x22;" />

<PyAttribute name="&#x22;nessie_api_version&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='v1', description='Nessie API version')&#x22;" />

<PyAttribute name="&#x22;nessie_default_ref&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='main', description='Default Nessie branch/tag')&#x22;" />

<PyAttribute name="&#x22;nessie_query_engine&#x22;" type="&#x22;str | None&#x22;" value="&#x22;Field(default=None, description='Optional query_engine capability name for catalog scan fallbacks')&#x22;" />

Functions [#functions]

<PyFunction name="&#x22;model_post_init&#x22;" type="&#x22;(self, __context) -> None&#x22;">
  Post-initialization hook to resolve host and port.

  <PySourceCode>
    ```python
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to resolve host and port."""
        host, port = resolve_host(self.nessie_host, self.nessie_port, port_env_var="NESSIE_PORT")
        object.__setattr__(self, "nessie_host", host)
        object.__setattr__(self, "nessie_port", port)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;__context&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;nessie_uri&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the base Nessie API URI.

  <PySourceCode>
    ```python
    def nessie_uri(self) -> str:
        """Return the base Nessie API URI.

        Returns:
            str: Base URI for Nessie API endpoints.

        """
        return f"http://{self.nessie_host}:{self.nessie_port}/api"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Base URI for Nessie API endpoints.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;nessie_api_uri&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the versioned Nessie API URI.

  <PySourceCode>
    ```python
    def nessie_api_uri(self) -> str:
        """Return the versioned Nessie API URI.

        Returns:
            str: Versioned URI for Nessie API endpoints.

        """
        return f"http://{self.nessie_host}:{self.nessie_port}/api/{self.nessie_api_version}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Versioned URI for Nessie API endpoints.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;nessie_iceberg_rest_uri&#x22;" type="&#x22;(self) -> str&#x22;">
  Return the Nessie Iceberg REST catalog URI.

  <PySourceCode>
    ```python
    def nessie_iceberg_rest_uri(self) -> str:
        """Return the Nessie Iceberg REST catalog URI.

        Returns:
            str: URI for Iceberg REST catalog integration.

        """
        return f"http://{self.nessie_host}:{self.nessie_port}/iceberg"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    URI for Iceberg REST catalog integration.
  </PyFunctionReturn>
</PyFunction>
