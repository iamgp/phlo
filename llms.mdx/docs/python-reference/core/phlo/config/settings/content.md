# settings (/docs/python-reference/core/phlo/config/settings)



Core application settings for Phlo.

This module defines the primary configuration settings used throughout the Phlo
framework. Settings are loaded from environment variables and `.phlo/.env` files
with validation via Pydantic.

All settings can be customized through environment variables or by creating
a `.phlo/.env` file in your project root.

<PyAttribute name="&#x22;config&#x22;" type="null" value="&#x22;_get_config()&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;Settings&#x22;" href="&#x22;/docs/python-reference/core/phlo/config/settings/Settings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_get_config&#x22;" type="&#x22;() -> Settings&#x22;">
      Get cached config instance.

      Uses lru\_cache to ensure config is loaded once and reused across
      the application lifecycle. This provides efficient access to settings
      without repeated file I/O or parsing.

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        This is an internal function. Use :func:`get_settings` for public access.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache
        def _get_config() -> Settings:
            """Get cached config instance.

            Uses lru_cache to ensure config is loaded once and reused across
            the application lifecycle. This provides efficient access to settings
            without repeated file I/O or parsing.

            Returns:
                Settings: Validated Settings instance with all configuration values.

            Note:
                This is an internal function. Use :func:`get_settings` for public access.

            """
            return Settings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.config.settings.Settings&#x22;">
        Validated Settings instance with all configuration values.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> Settings&#x22;">
      Get application settings.

      This is the recommended way to access configuration in application code.
      It returns a cached Settings instance and supports future dependency
      injection patterns for testing.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo.config import get_settings

        settings = get_settings()
        if settings.phlo_environment == "production":
            # Apply production-specific logic
            pass
        ```
      </Callout>

      <PySourceCode>
        ````python
        def get_settings() -> Settings:
            """Get application settings.

            This is the recommended way to access configuration in application code.
            It returns a cached Settings instance and supports future dependency
            injection patterns for testing.

            Returns:
                Settings: Validated Settings instance with all configuration values.

            Example:
                \```python
                from phlo.config import get_settings

                settings = get_settings()
                if settings.phlo_environment == "production":
                    # Apply production-specific logic
                    pass
                \```

            """
            return _get_config()
        ````
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.config.settings.Settings&#x22;">
        Validated Settings instance with all configuration values.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
