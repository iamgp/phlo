# phlo-core-plugins

Core plugins package for Phlo containing essential quality checks and source connectors.

## Description

Bundled plugins for common data quality checks and a generic REST API source connector.

## Installation

```bash
pip install phlo-core-plugins
```

This package is installed automatically with Phlo.

## Included Plugins

### Quality Checks

| Plugin             | Description                                 |
| ------------------ | ------------------------------------------- |
| `null_check`       | Validates column completeness (no nulls)    |
| `uniqueness_check` | Validates primary key uniqueness            |
| `freshness_check`  | Validates data freshness against timestamps |
| `schema_check`     | Validates data against expected schema      |

### Source Connectors

| Plugin     | Description                                            |
| ---------- | ------------------------------------------------------ |
| `rest_api` | Generic REST API connector with configurable endpoints |

## Usage

```python
from phlo.plugins import get_quality_check

null_check = get_quality_check("null_check")
check = null_check.create_check(columns=["id", "name"])
```
