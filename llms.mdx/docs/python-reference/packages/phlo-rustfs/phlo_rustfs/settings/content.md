# settings (/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/settings)



RustFS settings.

This module defines the configuration schema and defaults for connecting to
RustFS (S3-compatible object storage). Settings are loaded from environment
variables and validated using Pydantic.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;RustfsSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-rustfs/phlo_rustfs/settings/RustfsSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> RustfsSettings&#x22;">
      Return cached RustFS settings.

      Factory function returning a singleton RustfsSettings instance.
      Uses functools.lru\_cache to ensure only one instance is created
      per process, improving performance and consistency.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > settings = get\_settings()
        > > > same\_settings = get\_settings()
        > > > settings is same\_settings
        > > > True
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> RustfsSettings:
            """Return cached RustFS settings.

            Factory function returning a singleton RustfsSettings instance.
            Uses functools.lru_cache to ensure only one instance is created
            per process, improving performance and consistency.

            Returns:
                Cached RustfsSettings instance.

            Example:
                >>> settings = get_settings()
                >>> same_settings = get_settings()
                >>> settings is same_settings
                True

            """
            return RustfsSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_rustfs.settings.RustfsSettings&#x22;">
        Cached RustfsSettings instance.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
