# settings (/docs/python-reference/packages/phlo-postgres/phlo_postgres/settings)



PostgreSQL connection settings and configuration.

This module provides Pydantic-based settings management for PostgreSQL connections,
including support for connection string generation and host/port resolution via
the phlo configuration system.

Example:

> > > from phlo\_postgres.settings import get\_settings
> > > settings = get\_settings()
> > > conn\_str = settings.get\_postgres\_connection\_string()
> > > print(conn\_str)
> > > postgresql://phlo:phlo\@postgres:5432/phlo

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PostgresSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-postgres/phlo_postgres/settings/PostgresSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> PostgresSettings&#x22;">
      Return cached PostgreSQL settings instance.

      Provides a singleton-style access to PostgreSQL settings with LRU caching
      to avoid repeated parsing of environment variables and configuration files.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        The cache size of 1 ensures the same settings object is returned
        throughout the process lifetime. Settings are loaded once on first
        call and reused thereafter.
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > settings1 = get\_settings()
        > > > settings2 = get\_settings()
        > > > settings1 is settings2  # Same cached instance
        > > > True
        > > >
        > > > Access connection parameters [#access-connection-parameters]
        > > >
        > > > settings = get\_settings()
        > > > print(f"Connecting to \{settings.postgres\_host}:\{settings.postgres\_port}")
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> PostgresSettings:
            """Return cached PostgreSQL settings instance.

            Provides a singleton-style access to PostgreSQL settings with LRU caching
            to avoid repeated parsing of environment variables and configuration files.

            Returns:
                PostgresSettings: Cached settings instance.

            Note:
                The cache size of 1 ensures the same settings object is returned
                throughout the process lifetime. Settings are loaded once on first
                call and reused thereafter.

            Example:
                >>> settings1 = get_settings()
                >>> settings2 = get_settings()
                >>> settings1 is settings2  # Same cached instance
                True
                >>>
                >>> # Access connection parameters
                >>> settings = get_settings()
                >>> print(f"Connecting to {settings.postgres_host}:{settings.postgres_port}")

            """
            return PostgresSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_postgres.settings.PostgresSettings&#x22;">
        Cached settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
