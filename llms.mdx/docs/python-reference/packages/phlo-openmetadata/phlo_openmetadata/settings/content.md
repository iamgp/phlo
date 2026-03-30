# settings (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/settings)



OpenMetadata settings configuration.

Provides Pydantic-based configuration management for OpenMetadata integration,
including server connection settings, authentication credentials, and sync options.

Example:

> > > from phlo\_openmetadata.settings import OpenMetadataSettings, get\_settings
> > > settings = get\_settings()
> > > settings.openmetadata\_uri()
> > > '[http://openmetadata-server:8585/api](http://openmetadata-server:8585/api)'

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;OpenMetadataSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/settings/OpenMetadataSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> OpenMetadataSettings&#x22;">
      Get cached OpenMetadata settings.

      Returns a cached instance to avoid repeated configuration loading.
      The cache is limited to 1 entry as settings are typically global.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> OpenMetadataSettings:
            """Get cached OpenMetadata settings.

            Returns a cached instance to avoid repeated configuration loading.
            The cache is limited to 1 entry as settings are typically global.

            Returns:
                OpenMetadataSettings: Cached OpenMetadata settings instance.

            """
            return OpenMetadataSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_openmetadata.settings.OpenMetadataSettings&#x22;">
        Cached OpenMetadata settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
