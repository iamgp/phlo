# adapters (/docs/python-reference/core/phlo/migrations/adapters)



Source adapters for data migration reads.

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SourceAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/migrations/adapters/SourceAdapter&#x22;" />

      <Card title="&#x22;CsvSourceAdapter&#x22;" href="&#x22;/docs/python-reference/core/phlo/migrations/adapters/CsvSourceAdapter&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_source_adapter&#x22;" type="&#x22;(source_type) -> SourceAdapter | None&#x22;">
      Resolve a source adapter from built-ins and registered capabilities.

      <PySourceCode>
        ```python
        def resolve_source_adapter(source_type: str) -> SourceAdapter | None:
            """Resolve a source adapter from built-ins and registered capabilities."""
            adapter = _BUILTIN_ADAPTERS.get(source_type)
            if adapter is not None:
                return adapter

            for spec in get_capability_registry().list_data_migration_sources():
                if spec.name != source_type:
                    continue
                provider = spec.provider
                return provider if _is_source_adapter(provider) else None

            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;source_type&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.migrations.adapters.SourceAdapter | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;list_source_adapter_types&#x22;" type="&#x22;() -> list[str]&#x22;">
      List all known source adapter types.

      <PySourceCode>
        ```python
        def list_source_adapter_types() -> list[str]:
            """List all known source adapter types."""
            adapter_types = set(_BUILTIN_ADAPTERS.keys())
            for spec in get_capability_registry().list_data_migration_sources():
                adapter_types.add(spec.name)
            return sorted(adapter_types)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_is_source_adapter&#x22;" type="&#x22;(provider) -> bool&#x22;">
      <PySourceCode>
        ```python
        def _is_source_adapter(provider: Any) -> bool:
            return (
                hasattr(provider, "source_type")
                and hasattr(provider, "validate_config")
                and hasattr(provider, "read_chunks")
                and hasattr(provider, "estimate_row_count")
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;provider&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
