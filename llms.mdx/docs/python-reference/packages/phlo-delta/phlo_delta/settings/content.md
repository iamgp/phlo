# settings (/docs/python-reference/packages/phlo-delta/phlo_delta/settings)



Delta Lake settings and configuration management.

This module provides configuration management for Delta Lake storage,
including S3 endpoints, credentials, warehouse paths, and storage options.

Example:
from phlo\_delta.settings import get\_settings

settings = get\_settings()
storage\_opts = settings.get\_storage\_options()

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DeltaSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-delta/phlo_delta/settings/DeltaSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> DeltaSettings&#x22;">
      Get cached Delta Lake settings.

      Returns a singleton instance of DeltaSettings, cached for performance.
      The cached instance ensures consistent configuration across the application.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        settings = get\_settings()
        path = settings.delta\_warehouse\_path
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> DeltaSettings:
            """Get cached Delta Lake settings.

            Returns a singleton instance of DeltaSettings, cached for performance.
            The cached instance ensures consistent configuration across the application.

            Returns:
                DeltaSettings: Cached Delta Lake settings instance.

            Example:
                settings = get_settings()
                path = settings.delta_warehouse_path

            """
            return DeltaSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_delta.settings.DeltaSettings&#x22;">
        Cached Delta Lake settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
