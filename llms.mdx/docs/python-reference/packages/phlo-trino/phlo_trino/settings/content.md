# settings (/docs/python-reference/packages/phlo-trino/phlo_trino/settings)



Trino settings and configuration management.

This module provides configuration management for Trino connections,
including host resolution, port configuration, and DSN generation.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;TrinoSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/settings/TrinoSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;build_trino_dsn&#x22;" type="&#x22;(host, port, catalog) -> str&#x22;">
      Build a Trino DSN string.

      <PySourceCode>
        ```python
        def build_trino_dsn(host: str, port: int, catalog: str) -> str:
            """Build a Trino DSN string.

            Args:
                host: Trino hostname.
                port: Trino HTTP port.
                catalog: Trino catalog name.

            Returns:
                DSN string for Trino connections.

            """
            return f"trino://{host}:{port}/{catalog}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;host&#x22;" type="&#x22;str&#x22;" value="undefined">
          Trino hostname.
        </PyParameter>

        <PyParameter name="&#x22;port&#x22;" type="&#x22;int&#x22;" value="undefined">
          Trino HTTP port.
        </PyParameter>

        <PyParameter name="&#x22;catalog&#x22;" type="&#x22;str&#x22;" value="undefined">
          Trino catalog name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        DSN string for Trino connections.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> TrinoSettings&#x22;">
      Return cached Trino settings.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> TrinoSettings:
            """Return cached Trino settings.

            Returns:
                Trino settings instance.

            """
            return TrinoSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_trino.settings.TrinoSettings&#x22;">
        Trino settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
