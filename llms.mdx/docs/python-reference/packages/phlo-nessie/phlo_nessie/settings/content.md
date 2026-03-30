# settings (/docs/python-reference/packages/phlo-nessie/phlo_nessie/settings)



Nessie configuration settings module.

This module provides Pydantic-based configuration management for the Nessie
catalog service, including host resolution, port configuration, and URI builders
for various Nessie API endpoints.

Example:

> > > from phlo\_nessie.settings import get\_settings
> > > settings = get\_settings()
> > > print(settings.nessie\_uri())
> > > '[http://nessie:19120/api](http://nessie:19120/api)'

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;NessieSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-nessie/phlo_nessie/settings/NessieSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> NessieSettings&#x22;">
      Return cached Nessie settings.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> NessieSettings:
            """Return cached Nessie settings.

            Returns:
                NessieSettings: Singleton settings instance.

            """
            return NessieSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_nessie.settings.NessieSettings&#x22;">
        Singleton settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
