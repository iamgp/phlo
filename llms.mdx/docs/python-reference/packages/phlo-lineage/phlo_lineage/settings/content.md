# settings (/docs/python-reference/packages/phlo-lineage/phlo_lineage/settings)



Lineage settings and configuration management.

This module provides Pydantic-based configuration management for the phlo-lineage
package. It defines the LineageSettings class which handles environment variable
resolution for database connection strings and other lineage-related configuration.

Configuration Sources:
Settings are loaded from environment variables using Pydantic's
validation\_alias feature, which supports multiple fallback variable names.

Priority Order for lineage\_db\_url:

1. LINEAGE\_DB\_URL
2. PHLO\_LINEAGE\_DB\_URL
3. DAGSTER\_PG\_DB\_CONNECTION\_STRING

Usage:
Settings are accessed via the cached get\_settings() function, which returns
a singleton instance parsed from the environment.

Example:

> > > from phlo\_lineage.settings import get\_settings, LineageSettings
> > >
> > > Access cached settings [#access-cached-settings]
> > >
> > > settings = get\_settings()
> > > print(settings.lineage\_db\_url)
> > > 'postgresql://user:pass\@localhost:5432/phlo'
> > >
> > > Create settings directly (bypass cache) [#create-settings-directly-bypass-cache]
> > >
> > > settings = LineageSettings()  # Reads env vars fresh

Environment Variables:
LINEAGE\_DB\_URL: Primary lineage database URL.
PHLO\_LINEAGE\_DB\_URL: Fallback lineage database URL.
DAGSTER\_PG\_DB\_CONNECTION\_STRING: Dagster database URL (tertiary fallback).

See Also:
phlo.config.base.BaseConfig for the base configuration class.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/settings/LineageSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> LineageSettings&#x22;">
      Get cached LineageSettings instance.

      This function returns a singleton LineageSettings instance that is
      cached after first access using functools.lru\_cache. This ensures
      consistent settings across the application while avoiding repeated
      environment variable parsing.

      <Callout title="&#x22;Caching&#x22;" type="&#x22;caching&#x22;">
        Settings are cached with maxsize=1, meaning only one instance is
        stored. The cache is process-local and thread-safe.

        To reload settings (e.g., after environment changes):

        > > > get\_settings.cache\_clear()
        > > > new\_settings = get\_settings()
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > from phlo\_lineage.settings import get\_settings
        > > >
        > > > settings = get\_settings()
        > > > if settings.lineage\_db\_url:
        > > > ...     print("Lineage database configured")
        > > > ... else:
        > > > ...     print("No lineage database URL found")
      </Callout>

      <Callout title="&#x22;Thread Safety&#x22;" type="&#x22;thread-safety&#x22;">
        lru\_cache provides thread-safe caching. The LineageSettings
        instance itself is immutable after creation (frozen dataclass).
      </Callout>

      <Callout title="&#x22;Performance&#x22;" type="&#x22;performance&#x22;">
        First call: Parses environment variables (\~0.1-1ms)
        Subsequent calls: Returns cached instance (O(1))
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        functools.lru\_cache for caching behavior details.
      </Callout>

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> LineageSettings:
            """Get cached LineageSettings instance.

            This function returns a singleton LineageSettings instance that is
            cached after first access using functools.lru_cache. This ensures
            consistent settings across the application while avoiding repeated
            environment variable parsing.

            Returns:
                LineageSettings instance loaded from environment variables.

            Caching:
                Settings are cached with maxsize=1, meaning only one instance is
                stored. The cache is process-local and thread-safe.

                To reload settings (e.g., after environment changes):
                >>> get_settings.cache_clear()
                >>> new_settings = get_settings()

            Example:
                >>> from phlo_lineage.settings import get_settings
                >>>
                >>> settings = get_settings()
                >>> if settings.lineage_db_url:
                ...     print("Lineage database configured")
                ... else:
                ...     print("No lineage database URL found")

            Thread Safety:
                lru_cache provides thread-safe caching. The LineageSettings
                instance itself is immutable after creation (frozen dataclass).

            Performance:
                First call: Parses environment variables (~0.1-1ms)
                Subsequent calls: Returns cached instance (O(1))

            See Also:
                functools.lru_cache for caching behavior details.

            """
            return LineageSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_lineage.settings.LineageSettings&#x22;">
        LineageSettings instance loaded from environment variables.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
