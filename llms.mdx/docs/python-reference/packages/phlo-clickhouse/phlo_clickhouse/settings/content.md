# settings (/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/settings)



ClickHouse settings configuration.

This module provides Pydantic-based configuration management for ClickHouse
connection parameters, including host, port, authentication, and security settings.

Example:
Loading ClickHouse settings:

> > > from phlo\_clickhouse.settings import get\_settings, ClickHouseSettings
> > > settings = get\_settings()
> > > settings.clickhouse\_host
> > > 'clickhouse'

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ClickHouseSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-clickhouse/phlo_clickhouse/settings/ClickHouseSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> ClickHouseSettings&#x22;">
      Return cached ClickHouse settings instance.

      Uses functools.lru\_cache to ensure settings are loaded only once
      and reused across the application lifecycle.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > settings = get\_settings()
        > > > settings.clickhouse\_host
        > > > 'clickhouse'
        > > >
        > > > Subsequent calls return the same cached instance [#subsequent-calls-return-the-same-cached-instance]
        > > >
        > > > get\_settings() is settings
        > > > True
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> ClickHouseSettings:
            """Return cached ClickHouse settings instance.

            Uses functools.lru_cache to ensure settings are loaded only once
            and reused across the application lifecycle.

            Returns:
                ClickHouseSettings instance with loaded configuration.

            Example:
                >>> settings = get_settings()
                >>> settings.clickhouse_host
                'clickhouse'
                >>> # Subsequent calls return the same cached instance
                >>> get_settings() is settings
                True

            """
            return ClickHouseSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_clickhouse.settings.ClickHouseSettings&#x22;">
        ClickHouseSettings instance with loaded configuration.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
