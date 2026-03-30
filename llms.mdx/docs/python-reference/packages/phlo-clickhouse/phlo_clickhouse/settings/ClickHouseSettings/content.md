# ClickHouseSettings (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/settings/ClickHouseSettings)



ClickHouse data plane configuration model.

Configuration class for ClickHouse connection parameters using Pydantic
for validation and default value management.

Attributes [#attributes]

<PyAttribute name="&#x22;clickhouse_host&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='clickhouse', description='ClickHouse service hostname')&#x22;">
  Hostname or IP address of the ClickHouse server.
  Defaults to "clickhouse" for Docker Compose networking.
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_http_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=8123, description='ClickHouse HTTP interface port')&#x22;">
  HTTP interface port for ClickHouse.
  Defaults to 8123 (standard ClickHouse HTTP port).
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_native_port&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=19000, description='ClickHouse native protocol port')&#x22;">
  Native protocol port for ClickHouse.
  Defaults to 19000.
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_user&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='default', description='ClickHouse username')&#x22;">
  Username for ClickHouse authentication.
  Defaults to "default".
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_password&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='', description='ClickHouse password')&#x22;">
  Password for ClickHouse authentication.
  Defaults to empty string for unauthenticated connections.
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_db&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(default='default', description='Default ClickHouse database')&#x22;">
  Default database to connect to.
  Defaults to "default".
</PyAttribute>

<PyAttribute name="&#x22;clickhouse_secure&#x22;" type="&#x22;bool&#x22;" value="&#x22;Field(default=False, description='Use TLS for ClickHouse connections')&#x22;">
  Whether to use TLS/SSL for connections.
  Defaults to False.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;clickhouse_http_endpoint&#x22;" type="&#x22;(self) -> str&#x22;">
  Return host:port endpoint for ClickHouse HTTP interface.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > settings = ClickHouseSettings(clickhouse\_host="localhost", clickhouse\_http\_port=8123)
    > > > settings.clickhouse\_http\_endpoint()
    > > > 'localhost:8123'
  </Callout>

  <PySourceCode>
    ```python
    def clickhouse_http_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse HTTP interface.

        Returns:
            Formatted endpoint string "host:port" for HTTP connections.

        Example:
            >>> settings = ClickHouseSettings(clickhouse_host="localhost", clickhouse_http_port=8123)
            >>> settings.clickhouse_http_endpoint()
            'localhost:8123'

        """
        return f"{self.clickhouse_host}:{self.clickhouse_http_port}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted endpoint string "host:port" for HTTP connections.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;clickhouse_native_endpoint&#x22;" type="&#x22;(self) -> str&#x22;">
  Return host:port endpoint for ClickHouse native interface.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    > > > settings = ClickHouseSettings(clickhouse\_host="localhost", clickhouse\_native\_port=9000)
    > > > settings.clickhouse\_native\_endpoint()
    > > > 'localhost:9000'
  </Callout>

  <PySourceCode>
    ```python
    def clickhouse_native_endpoint(self) -> str:
        """Return host:port endpoint for ClickHouse native interface.

        Returns:
            Formatted endpoint string "host:port" for native protocol connections.

        Example:
            >>> settings = ClickHouseSettings(clickhouse_host="localhost", clickhouse_native_port=9000)
            >>> settings.clickhouse_native_endpoint()
            'localhost:9000'

        """
        return f"{self.clickhouse_host}:{self.clickhouse_native_port}"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Formatted endpoint string "host:port" for native protocol connections.
  </PyFunctionReturn>
</PyFunction>
