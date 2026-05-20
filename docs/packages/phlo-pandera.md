# phlo-pandera

Data quality checks and validation for Phlo.

## Overview

`phlo-pandera` enables defining and executing data quality checks using the `phlo.quality.pandera(...)` decorator. Checks emit capability specs that adapters translate into orchestrator-native checks.

## Installation

```bash
pip install phlo-pandera
# or
phlo plugin install quality
```

## Configuration

| Variable                 | Default | Description                    |
| ------------------------ | ------- | ------------------------------ |
| `PANDERA_CRITICAL_LEVEL` | `error` | Severity that blocks promotion |

## Features

### Auto-Configuration

| Feature                 | How It Works                                              |
| ----------------------- | --------------------------------------------------------- |
| **Check Discovery**     | Quality workflows auto-discovered in `workflows/quality/` |
| **Event Emission**      | Emits `quality.result` events to HookBus                  |
| **Adapter Integration** | Checks translate into orchestrator-native checks via adapters |
| **Alerting**            | Failed checks auto-routed to alerting destinations        |

### Event Flow

```
phlo.quality.pandera(...) → QualityEventEmitter → quality.result → [Alerting, Metrics, OpenMetadata]
```

## Usage

### Defining Checks

```python
import phlo
from phlo.contracts import Consumer, SLA
from phlo.quality import NullCheck, UniqueCheck, RangeCheck

@phlo.quality.pandera(
    table="bronze.users",
    checks=[
        NullCheck(columns=["id"]),
        UniqueCheck(columns=["email"]),
        RangeCheck(column="age", min_value=0, max_value=150),
    ],
    owner="data-quality",
    consumers=[
        Consumer(name="finance_dashboard"),
        "ml_feature_store",
    ],
    sla=SLA(freshness_hours=4, quality_threshold=0.995),
)
def validate_users():
    pass
```

### Helper Factories

`phlo-pandera` exposes helper factories that turn contracts into common checks:

```python
from phlo.contracts import SLA
from phlo_pandera import checks_from_contract

checks = checks_from_contract(
    schema=UserSchema,
    unique_key="id",
    sla=SLA(freshness_hours=24),
    freshness_column="updated_at",
)
```

| Helper | Purpose |
| --- | --- |
| `required_field_null_checks` | Generate null checks from non-nullable schema fields. |
| `unique_key_check` | Generate uniqueness checks for one or more key columns. |
| `freshness_check_from_sla` | Generate freshness checks from `SLA.freshness_hours`. |
| `accepted_values_check` | Generate a custom SQL accepted-values check. |
| `checks_from_contract` | Combine schema, key, and SLA metadata into checks. |

### Decorator Options

| Option              | Type                           | Description                                              |
| ------------------- | ------------------------------ | -------------------------------------------------------- |
| `table`             | `str`                          | Fully-qualified table to validate (for example `bronze.users`) |
| `checks`            | `list[QualityCheck]`           | Checks to execute                                        |
| `asset_key`         | `str \| None`                  | Override asset key (derived from table by default)     |
| `group`             | `str \| None`                  | Optional asset group                                     |
| `blocking`          | `bool`                         | Whether failed checks block downstream (default: True) |
| `partition_aware`   | `bool`                         | Scope checks to active partition when available (default: True) |
| `warn_threshold`    | `float`                        | Max failed-check fraction for WARN vs ERROR (default: 0.0) |
| `partition_column`  | `str`                          | Partition column for scoping queries (default: `_phlo_partition_date`) |
| `rolling_window_days`| `int \| None`                 | Scope to last N days when unpartitioned (default: 7)     |
| `full_table`        | `bool`                         | Disable partition scoping (default: False)               |
| `description`       | `str \| None`                  | Auto-generated if not provided                           |
| `query`             | `str \| None`                  | Custom SQL query (defaults to `SELECT * FROM {table}`) |
| `backend`           | `str`                          | Query backend: `"trino"` or `"duckdb"` (default: `"trino"`) |
| `owner`             | `str \| None`                  | Optional owner/team metadata for contracts             |
| `consumers`         | `list[Consumer \| str] \| None`| Optional downstream consumer metadata                    |
| `sla`               | `SLA \| None`                  | Optional freshness/quality contract metadata             |

### Using Pandera Schemas

```python
import pandera as pa
from pandera.typing import Series

import phlo

class UserSchema(pa.DataFrameModel):
    id: Series[str] = pa.Field(nullable=False, unique=True)
    email: Series[str] = pa.Field(nullable=False)
    age: Series[int] = pa.Field(ge=0, le=150)

    class Config:
        strict = True
        coerce = True

# Use with ingestion decorator for automatic validation
@phlo.ingest.dlt(
    table_name="users",
    validation_schema=UserSchema,
    # ...
)
def ingest_users():
    pass
```

### CLI Commands

```bash
# List discovered schemas
phlo schema list

# Show schema details
phlo schema show OrderSchema

# Validate a schema file
phlo schema validate workflows/schemas/users.py

# Compare schema versions
phlo schema diff OrderSchema --old HEAD~1
```

## Built-in Checks

| Check             | Description                         | Example                                                              |
| ----------------- | ----------------------------------- | -------------------------------------------------------------------- |
| `NullCheck`       | Validates column has no NULL values | `NullCheck(columns=["id"])`                                          |
| `UniqueCheck`     | Validates column values are unique  | `UniqueCheck(columns=["email"])`                                     |
| `RangeCheck`      | Validates values are within range   | `RangeCheck(column="age", min_value=0, max_value=150)`               |
| `PatternCheck`    | Validates values match pattern      | `PatternCheck(column="email", pattern=r".*@.*\..*")`                 |
| `FreshnessCheck`  | Validates data is recent            | `FreshnessCheck(column="updated_at", max_age_hours=24)`              |
| `CountCheck`      | Validates row count                 | `CountCheck(min_rows=100, max_rows=10000)`                           |
| `CustomSQLCheck`  | Arbitrary SQL validation            | `CustomSQLCheck(sql="SELECT COUNT(*) FROM ... WHERE ...")`           |

## Quality Check Contract

For integration with Observatory and monitoring:

- Pandera schema checks use the name `pandera_contract`
- dbt test checks use the name `dbt__<test_type>__<target>`
- Checks emit metadata: `source`, `partition_key`, `failed_count`, `total_count`, `query_or_sql`, `sample` (≤ 20 rows)
- Checks may emit `repro_sql` for Trino reproduction
- Partitioned runs scope checks to the partition by default

## Custom Checks

Create custom quality check plugins:

```python
from phlo.plugins.base import QualityCheckPlugin, PluginMetadata

class MyCustomCheck(QualityCheckPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_custom_check",
            version="1.0.0",
            description="Custom validation logic"
        )

    def create_check(self, **kwargs):
        return CustomCheckInstance(**kwargs)
```

See [Plugin Development Guide](../guides/plugin-development.md) for details.

## Entry Points

| Entry Point                   | Plugin                    |
| ----------------------------- | ------------------------- |
| `phlo.plugins.quality_providers` | `PanderaQualityProvider` |
| `phlo.plugins.cli`           | Quality CLI commands      |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Dagster adapter for capability specs
- [phlo-alerting](phlo-alerting.md) - Alert routing
- [phlo-openmetadata](phlo-openmetadata.md) - Data catalog

## Next Steps

- [Testing Strategy Guide](../guides/testing-strategy.md) - Testing approaches
- [Best Practices](../operations/best-practices.md) - Production patterns
- [Developer Guide](../guides/developer-guide.md) - Decorator usage
