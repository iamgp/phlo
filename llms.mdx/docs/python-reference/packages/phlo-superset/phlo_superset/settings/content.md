# settings (/docs/python-reference/packages/phlo-superset/phlo_superset/settings)



Superset settings configuration.

This module defines the configuration schema and loading mechanisms for
Apache Superset integration within the Phlo platform. Settings are managed
through Pydantic models with environment variable support.

Example:

> > > from phlo\_superset.settings import SupersetSettings, get\_settings
> > > settings = get\_settings()
> > > print(f"Superset available at port \{settings.superset\_port}")
> > > 'Superset available at port 10007'

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SupersetSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-superset/phlo_superset/settings/SupersetSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> SupersetSettings&#x22;">
      Get cached Superset settings.

      This function returns a cached instance of SupersetSettings to avoid
      repeated configuration loading and parsing. The cache ensures that
      settings are loaded once per process and reused thereafter.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > settings = get\_settings()
        > > > settings2 = get\_settings()
        > > > settings is settings2  # Same cached instance
        > > > True
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        The LRU cache ensures only one settings instance exists per process.
        For testing purposes, use functools.cache\_clear() if needed.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> SupersetSettings:
            """Get cached Superset settings.

            This function returns a cached instance of SupersetSettings to avoid
            repeated configuration loading and parsing. The cache ensures that
            settings are loaded once per process and reused thereafter.

            Returns:
                Loaded Superset configuration settings instance.

            Raises:
                None

            Example:
                >>> settings = get_settings()
                >>> settings2 = get_settings()
                >>> settings is settings2  # Same cached instance
                True

            Note:
                The LRU cache ensures only one settings instance exists per process.
                For testing purposes, use functools.cache_clear() if needed.

            """
            return SupersetSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_superset.settings.SupersetSettings&#x22;">
        Loaded Superset configuration settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
