# settings (/docs/python-reference/packages/phlo-alerting/phlo_alerting/settings)



Alerting settings configuration.

This module provides configuration management for the phlo-alerting package
using Pydantic models. It supports configuration via environment variables
with automatic type validation and default values.

All configuration values are read from environment variables with the
"PHLO\_ALERT\_" prefix. The get\_settings() function provides a cached
singleton instance for efficient repeated access.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;AlertingSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-alerting/phlo_alerting/settings/AlertingSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> AlertingSettings&#x22;">
      Return cached alerting settings instance.

      Provides a singleton AlertingSettings instance with caching for
      efficient repeated access. The instance is created once and reused
      across the application lifecycle.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> AlertingSettings:
            """Return cached alerting settings instance.

            Provides a singleton AlertingSettings instance with caching for
            efficient repeated access. The instance is created once and reused
            across the application lifecycle.

            Returns:
                AlertingSettings instance with loaded configuration.

            Examples:
                >>> settings1 = get_settings()
                >>> settings2 = get_settings()
                >>> settings1 is settings2
                True

            """
            return AlertingSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_alerting.settings.AlertingSettings&#x22;">
        AlertingSettings instance with loaded configuration.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
