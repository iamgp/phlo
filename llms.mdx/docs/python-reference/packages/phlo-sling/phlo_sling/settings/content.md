# settings (/docs/python-reference/packages/phlo-sling/phlo_sling/settings)



Settings for phlo-sling package.

This module defines the configuration settings for the phlo-sling package,
including defaults for replication modes, namespace handling, and connection
management. Settings are loaded from environment variables and configuration
files with sensible defaults.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SlingSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-sling/phlo_sling/settings/SlingSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> SlingSettings&#x22;">
      Return cached Sling settings instance.

      Returns a singleton instance of SlingSettings using LRU caching to
      avoid repeated configuration loading. The settings are loaded from
      environment variables and configuration files on first access.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Get settings in application code::

        settings = get\_settings()
        namespace = settings.sling\_default\_namespace
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> SlingSettings:
            """Return cached Sling settings instance.

            Returns a singleton instance of SlingSettings using LRU caching to
            avoid repeated configuration loading. The settings are loaded from
            environment variables and configuration files on first access.

            Returns:
                Cached SlingSettings instance with loaded configuration values.

            Example:
                Get settings in application code::

                    settings = get_settings()
                    namespace = settings.sling_default_namespace

            """
            return SlingSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_sling.settings.SlingSettings&#x22;">
        Cached SlingSettings instance with loaded configuration values.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
