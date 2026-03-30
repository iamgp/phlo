# phlo (/docs/python-reference/core/phlo)



Phlo - A modern data lakehouse platform.

Phlo is a decorator-driven data lakehouse framework that combines Apache Iceberg,
Project Nessie, Trino, dbt, and Dagster into an integrated platform.

This package provides the core Phlo API with lazy-loaded exports to avoid
circular dependencies during plugin discovery. All major functionality is
available through this top-level module.

Key Features:

* Write-Audit-Publish pattern with Git-like branching
* Type-safe data quality with automatic validation
* Production-ready patterns out of the box
* Schema-first development with Pandera

Lazy-Loaded Modules:
The following modules are loaded on first access to avoid circular imports:

* `phlo.ingestion`: Data ingestion operations
* `phlo.quality`: Data quality validation
* `phlo.metrics`: Platform metrics collection

Direct Exports:

* :class:`Consumer`: Data consumer contract
* :class:`SLA`: Service level agreement contract
* :func:`phlo_ingestion`: Ingestion decorator
* :func:`get_ingestion_assets`: Retrieve ingestion assets
* :func:`phlo_quality`: Quality decorator
* :func:`get_quality_checks`: Retrieve quality checks
* Quality check classes: NullCheck, RangeCheck, FreshnessCheck, etc.

Plugin Entry Points:
Phlo uses the following entry point groups for plugin discovery:

* `phlo.sources`: Data source connectors
* `phlo.quality`: Quality check implementations
* `phlo.ingestion_providers`: Ingestion providers
* `phlo.transformation_providers`: Transformation providers
* `phlo.transforms`: Data transformation tools
* `phlo.services`: Infrastructure services
* `phlo.cli_commands`: CLI command extensions
* `phlo.hooks`: Hook handlers
* `phlo.catalogs`: Metadata catalogs
* `phlo.asset_providers`: Asset definitions
* `phlo.resource_providers`: Resource definitions
* `phlo.orchestrators`: Orchestrator adapters

Version Information:

* `__version__`: Current Phlo version string

Example:

```python
import phlo

# Access ingestion decorator
@phlo.ingestion.phlo_ingestion(source="api", table_name="events")
def load_events():
    return fetch_events()

# Access quality decorator
@phlo.quality.phlo_quality(schema=UserSchema)
def validate_users():
    return load_users()

# Access quality check classes
from phlo import NullCheck, RangeCheck
```

See Also:

* Documentation: [https://docs.phlo.dev](https://docs.phlo.dev)
* Repository: [https://github.com/phlohouse/phlo](https://github.com/phlohouse/phlo)
* Plugin API: :mod:`phlo.plugins.base`
* Configuration: :mod:`phlo.config`

Note:
This module uses `__getattr__` for lazy loading to prevent circular
imports during plugin discovery. All public exports are listed in `__all__`.

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;version('phlo')&#x22;" />

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['__version__', *_SUBMODULE_EXPORTS, *_CONTRACT_EXPORTS, *_INGESTION_EXPORTS, *_QUALITY_EXPORTS]&#x22;" />

<Tabs items="[&#x22;Functions&#x22;,&#x22;Modules&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;__getattr__&#x22;" type="&#x22;(name) -> Any&#x22;">
      Resolve top-level exports without importing optional packages eagerly.

      <PySourceCode>
        ```python
        def __getattr__(name: str) -> Any:
            """Resolve top-level exports without importing optional packages eagerly.

            Args:
                name: Attribute name requested from the phlo package.

            Returns:
                The requested attribute or module.

            Raises:
                AttributeError: If the attribute is not exported by this module.

            """
            if name in _SUBMODULE_EXPORTS:
                module = import_module(f"{__name__}.{name}")
                globals()[name] = module
                return module
            if name in _CONTRACT_EXPORTS:
                from phlo.contracts import SLA, Consumer

                globals().update({"Consumer": Consumer, "SLA": SLA})
                return globals()[name]
            if name in _INGESTION_EXPORTS:
                from phlo.ingestion import get_ingestion_assets, phlo_ingestion

                globals().update(
                    {
                        "get_ingestion_assets": get_ingestion_assets,
                        "phlo_ingestion": phlo_ingestion,
                    }
                )
                return globals()[name]
            if name in _QUALITY_EXPORTS:
                from phlo.quality import (
                    PANDERA_CONTRACT_CHECK_NAME,
                    AggregateConsistencyCheck,
                    AggregateSpec,
                    ChecksumReconciliationCheck,
                    CountCheck,
                    CustomSQLCheck,
                    FreshnessCheck,
                    KeyParityCheck,
                    MultiAggregateConsistencyCheck,
                    NullCheck,
                    PatternCheck,
                    QualityCheck,
                    QualityCheckContract,
                    RangeCheck,
                    ReconciliationCheck,
                    SchemaCheck,
                    UniqueCheck,
                    clear_quality_checks,
                    dbt_check_name,
                    get_quality_checks,
                    phlo_quality,
                )

                globals().update(
                    {
                        "AggregateConsistencyCheck": AggregateConsistencyCheck,
                        "AggregateSpec": AggregateSpec,
                        "ChecksumReconciliationCheck": ChecksumReconciliationCheck,
                        "CountCheck": CountCheck,
                        "CustomSQLCheck": CustomSQLCheck,
                        "FreshnessCheck": FreshnessCheck,
                        "KeyParityCheck": KeyParityCheck,
                        "MultiAggregateConsistencyCheck": MultiAggregateConsistencyCheck,
                        "NullCheck": NullCheck,
                        "PANDERA_CONTRACT_CHECK_NAME": PANDERA_CONTRACT_CHECK_NAME,
                        "PatternCheck": PatternCheck,
                        "QualityCheck": QualityCheck,
                        "QualityCheckContract": QualityCheckContract,
                        "RangeCheck": RangeCheck,
                        "ReconciliationCheck": ReconciliationCheck,
                        "SchemaCheck": SchemaCheck,
                        "UniqueCheck": UniqueCheck,
                        "clear_quality_checks": clear_quality_checks,
                        "dbt_check_name": dbt_check_name,
                        "get_quality_checks": get_quality_checks,
                        "phlo_quality": phlo_quality,
                    }
                )
                return globals()[name]
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Attribute name requested from the phlo package.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        The requested attribute or module.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;__dir__&#x22;" type="&#x22;() -> list[str]&#x22;">
      Return the list of available attributes for dir().

      <PySourceCode>
        ```python
        def __dir__() -> list[str]:
            """Return the list of available attributes for dir()."""
            return sorted(set(__all__))
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>
  </Tab>

  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/core/phlo/schema_registry&#x22;" title="&#x22;schema_registry&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/metrics&#x22;" title="&#x22;metrics&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/utils&#x22;" title="&#x22;utils&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/ingestion&#x22;" title="&#x22;ingestion&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/exceptions&#x22;" title="&#x22;exceptions&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/config_schema&#x22;" title="&#x22;config_schema&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/logging&#x22;" title="&#x22;logging&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/quality&#x22;" title="&#x22;quality&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/contracts&#x22;" title="&#x22;contracts&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/cli&#x22;" title="&#x22;cli&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/infrastructure&#x22;" title="&#x22;infrastructure&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/migrations&#x22;" title="&#x22;migrations&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/config&#x22;" title="&#x22;config&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/plugins&#x22;" title="&#x22;plugins&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/hooks&#x22;" title="&#x22;hooks&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/rbac&#x22;" title="&#x22;rbac&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/operations&#x22;" title="&#x22;operations&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/orchestrators&#x22;" title="&#x22;orchestrators&#x22;" />

      <Card href="&#x22;/docs/python-reference/core/phlo/capabilities&#x22;" title="&#x22;capabilities&#x22;" />
    </Cards>
  </Tab>
</Tabs>
