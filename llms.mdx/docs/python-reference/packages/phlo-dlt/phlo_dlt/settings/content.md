# settings (/docs/python-reference/packages/phlo-dlt/phlo_dlt/settings)



Settings for phlo-dlt package.

This module provides configuration management for the phlo-dlt package
using Pydantic settings. It defines default values and allows customization
via environment variables or configuration files.

Key Components:

* :class:`DltSettings`: Pydantic settings class for DLT configuration
* :func:`get_settings`: Cached factory for settings instance

Configuration Options:

* dlt\_default\_namespace: Default schema/namespace for table names

Environment Variables:
Settings can be configured via environment variables with the prefix
`PHLO_DLT_` (e.g., `PHLO_DLT_DEFAULT_NAMESPACE`).

See Also:

* :mod:`phlo.config.base`: Base configuration class
* :mod:`phlo_dlt.registry`: Uses settings for namespace resolution
* Pydantic Settings: [https://docs.pydantic.dev/latest/concepts/settings/](https://docs.pydantic.dev/latest/concepts/settings/)

Example:

```python
from phlo_dlt.settings import get_settings

settings = get_settings()
print(settings.dlt_default_namespace)  # "raw"
```

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DltSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/settings/DltSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> DltSettings&#x22;">
      Return cached DLT settings instance.

      Factory function that returns a singleton DltSettings instance.
      Uses functools.lru\_cache to ensure only one settings object is created
      per process, improving performance and ensuring consistency.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt.settings import get_settings

        # First call creates the instance
        settings = get_settings()

        # Subsequent calls return the same instance
        settings2 = get_settings()
        assert settings is settings2  # True
        ```
      </Callout>

      <PySourceCode>
        ````python
        @lru_cache(maxsize=1)
        def get_settings() -> DltSettings:
            """Return cached DLT settings instance.

            Factory function that returns a singleton DltSettings instance.
            Uses functools.lru_cache to ensure only one settings object is created
            per process, improving performance and ensuring consistency.

            Returns:
                DltSettings: The cached settings instance.

            Example:
                \```python
                from phlo_dlt.settings import get_settings

                # First call creates the instance
                settings = get_settings()

                # Subsequent calls return the same instance
                settings2 = get_settings()
                assert settings is settings2  # True
                \```

            """
            return DltSettings()
        ````
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_dlt.settings.DltSettings&#x22;">
        The cached settings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
