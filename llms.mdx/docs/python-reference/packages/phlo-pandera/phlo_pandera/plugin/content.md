# plugin (/docs/python-reference/packages/phlo-pandera/phlo_pandera/plugin)



Pandera quality provider plugin.

This module implements the PanderaQualityProvider plugin class that integrates
the Phlo Quality Framework with Phlo's plugin system. The provider exposes:

1. **Decorator**: The `@phlo_pandera` decorator for declarative quality checks
2. **Check Classes**: All built-in quality check implementations
3. **Schema Extractor**: PanderaSchemaExtractor for schema normalization
4. **Reconciliation Checks**: Cross-table validation checks

The plugin is registered via the `phlo.quality_providers` entry point and is
discovered automatically by Phlo's plugin system.

Example:
The plugin is typically not used directly. Instead, users interact with
the public API from `phlo_pandera`:

```python
from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

@phlo_pandera(
    table="bronze.events",
    checks=[
        NullCheck(columns=["event_id"]),
        RangeCheck(column="value", min_value=0, max_value=100),
    ],
)
def event_quality():
    pass
```

Plugin Registration:
The plugin is registered in `pyproject.toml`:

```toml
[project.entry-points."phlo.quality_providers"]
pandera = "phlo_pandera.plugin:PanderaQualityProvider"
```

See Also:

* `__init__.py`: Public API exports
* `decorator.py`: `@phlo_pandera` implementation
* `checks.py`: Core quality check classes
* `reconciliation.py`: Cross-table reconciliation checks

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PanderaQualityProvider&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/plugin/PanderaQualityProvider&#x22;" />
    </Cards>
  </Tab>
</Tabs>
