# settings (/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings)



Observatory UI settings and configuration.

This module provides the settings infrastructure for the Observatory UI package,
including database connection configuration for persistent settings storage.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;ObservatorySettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-observatory/phlo_observatory/settings/ObservatorySettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> ObservatorySettings&#x22;">
      Return cached Observatory settings instance.

      Settings are parsed from environment variables using PHLO\_OBSERVATORY\_\*
      prefixes and cached for the lifetime of the process.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > settings = get\_settings()
        > > > db\_url = settings.observatory\_settings\_db\_url
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> ObservatorySettings:
            """Return cached Observatory settings instance.

            Settings are parsed from environment variables using PHLO_OBSERVATORY_*
            prefixes and cached for the lifetime of the process.

            Returns:
                ObservatorySettings: Parsed and validated Observatory settings.

            Example:
                >>> settings = get_settings()
                >>> db_url = settings.observatory_settings_db_url

            """

            return ObservatorySettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_observatory.settings.ObservatorySettings&#x22;">
        Parsed and validated Observatory settings.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
