# phlo-core-plugins

Core plugins for Phlo (quality checks and source connectors).

## Overview

`phlo-core-plugins` provides built-in quality check plugins and source connectors. These are registered via entry points and auto-discovered at runtime.

## Installation

```bash
pip install phlo-core-plugins
# or included with phlo by default
```

## Features

### Auto-Configuration

| Feature               | How It Works                                            |
| --------------------- | ------------------------------------------------------- |
| **Quality Checks**    | Auto-registered via `phlo.plugins.quality` entry points |
| **Source Connectors** | Auto-registered via `phlo.plugins.sources` entry points |

## Quality Check Plugins

| Check              | Entry Point            | Description              |
| ------------------ | ---------------------- | ------------------------ |
| `null_check`       | `phlo.plugins.quality` | Validates no NULL values |
| `uniqueness_check` | `phlo.plugins.quality` | Validates unique values  |
| `range_check`      | `phlo.plugins.quality` | Validates value ranges   |
| `regex_check`      | `phlo.plugins.quality` | Validates regex patterns |
| `freshness_check`  | `phlo.plugins.quality` | Validates data freshness |

### Quality Check Usage

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

## Source Connector Plugins

| Connector  | Entry Point            | Description                |
| ---------- | ---------------------- | -------------------------- |
| `rest_api` | `phlo.plugins.sources` | Generic REST API connector |

### Source Connector Usage

```python
from phlo import phlo_ingestion

@phlo_ingestion(
    name="api_data",
    source="rest_api",  # Uses rest_api connector
    destination="bronze.api_data"
)
def ingest_api():
    return {
        "client": {"base_url": "https://api.example.com"},
        "resources": ["users", "events"]
    }
```

## Detailed Plugin Reference

### null_check

Validates that a column contains no NULL values.

```python
null_check(
    column="id",           # Column to check
    tolerance=0.0          # Allowed fraction of nulls (0.0-1.0)
)
```

### uniqueness_check

Validates that values in a column are unique.

```python
uniqueness_check(
    column="email",        # Column to check
    tolerance=0.0          # Allowed fraction of duplicates
)
```

### range_check

Validates that numeric values fall within a range.

```python
range_check(
    column="age",
    min_value=0,           # Minimum allowed value
    max_value=150,         # Maximum allowed value
    tolerance=0.0          # Allowed fraction of violations
)
```

### regex_check

Validates that string values match a pattern.

```python
regex_check(
    column="email",
    pattern=r"^[\w.-]+@[\w.-]+\.\w+$",  # Regex pattern
    tolerance=0.0
)
```

### freshness_check

Validates that data is recent.

```python
freshness_check(
    column="updated_at",   # Timestamp column
    max_age_hours=24       # Maximum age in hours
)
```

## Entry Points

| Entry Point            | Plugins                  |
| ---------------------- | ------------------------ |
| `phlo.plugins.quality` | Quality check plugins    |
| `phlo.plugins.sources` | Source connector plugins |

## Related Packages

- [phlo-quality](phlo-quality.md) - Quality framework
- [phlo-dlt](phlo-dlt.md) - Ingestion framework

## Next Steps

- [Plugin Development Guide](../guides/plugin-development.md) - Create custom plugins
- [Testing Strategy](../guides/testing-strategy.md) - Test quality checks
