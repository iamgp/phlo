# settings (/docs/python-reference/packages/phlo-dbt/phlo_dbt/settings)



dbt settings and configuration management.

This module provides Pydantic-based configuration management for dbt integration
within the Phlo platform. It handles query engine settings, project paths, and
derived artifact locations.

Example:

> > > from phlo\_dbt.settings import get\_settings, DbtSettings
> > > settings = get\_settings()
> > > print(f"Project: \{settings.dbt\_project\_path}")
> > > print(f"Catalog: \{settings.dbt\_query\_catalog}")
> > >
> > > Create custom settings [#create-custom-settings]
> > >
> > > custom = DbtSettings(dbt\_query\_catalog="analytics", dbt\_query\_threads=8)

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/settings/DbtSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> DbtSettings&#x22;">
      Return cached dbt settings.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> DbtSettings:
            """Return cached dbt settings.

            Returns:
                Singleton dbt settings instance.

            """
            return DbtSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_dbt.settings.DbtSettings&#x22;">
        Singleton dbt settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
