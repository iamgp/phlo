# phlo-quality

Data quality checks and validation for Phlo.

## Overview

`phlo-quality` enables defining and executing data quality checks using the `@phlo_quality` decorator. Checks run as Dagster asset checks and results are emitted to alerting, metrics, and data catalog systems.

## Installation

```bash
pip install phlo-quality
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
| **Dagster Integration** | Checks run as Dagster asset checks                        |
| **Alerting**            | Failed checks auto-routed to alerting destinations        |

### Event Flow

```
@phlo_quality → QualityEventEmitter → quality.result → [Alerting, Metrics, OpenMetadata]
```

## Usage

### Defining Checks

```python
from phlo import phlo_quality
from phlo_quality.checks import null_check, uniqueness_check, range_check

@phlo_quality(
    asset="bronze.users",
    checks=[
        null_check(column="id"),
        uniqueness_check(column="email"),
        range_check(column="age", min_value=0, max_value=150),
    ]
)
def validate_users():
    pass
```

### Using Pandera Schemas

```python
import pandera as pa
from pandera.typing import Series

class UserSchema(pa.DataFrameModel):
    id: Series[str] = pa.Field(nullable=False, unique=True)
    email: Series[str] = pa.Field(nullable=False)
    age: Series[int] = pa.Field(ge=0, le=150)

    class Config:
        strict = True
        coerce = True

# Use with @phlo_ingestion for automatic validation
@phlo_ingestion(
    table_name="users",
    validation_schema=UserSchema,
    # ...
)
def ingest_users():
    pass
```

### CLI Commands

```bash
# Run quality checks
phlo quality run --asset bronze.users

# List available checks
phlo quality list

# Run all quality checks
phlo quality run --all
```

## Built-in Checks

| Check              | Description                         | Example                                                      |
| ------------------ | ----------------------------------- | ------------------------------------------------------------ |
| `null_check`       | Validates column has no NULL values | `null_check(column="id")`                                    |
| `uniqueness_check` | Validates column values are unique  | `uniqueness_check(column="email")`                           |
| `range_check`      | Validates values are within range   | `range_check(column="age", min_value=0, max_value=150)`      |
| `regex_check`      | Validates values match pattern      | `regex_check(column="email", pattern=r".*@.*\..*")`          |
| `freshness_check`  | Validates data is recent            | `freshness_check(column="updated_at", max_age_hours=24)`     |
| `count_check`      | Validates row count                 | `count_check(min_rows=100, max_rows=10000)`                  |
| `custom_sql_check` | Arbitrary SQL validation            | `custom_sql_check(sql="SELECT COUNT(*) FROM ... WHERE ...")` |

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

| Entry Point            | Plugin                 |
| ---------------------- | ---------------------- |
| `phlo.plugins.cli`     | `quality` CLI commands |
| `phlo.plugins.quality` | Built-in check plugins |

## Related Packages

- [phlo-dagster](phlo-dagster.md) - Orchestration platform
- [phlo-alerting](phlo-alerting.md) - Alert routing
- [phlo-openmetadata](phlo-openmetadata.md) - Data catalog

## Next Steps

- [Testing Strategy Guide](../guides/testing-strategy.md) - Testing approaches
- [Best Practices](../operations/best-practices.md) - Production patterns
- [Developer Guide](../guides/developer-guide.md) - Decorator usage
