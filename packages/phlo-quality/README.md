# phlo-quality

Data quality checks and validation for Phlo.

## Description

Define and execute data quality checks using the `@phlo_quality` decorator. Checks run as Dagster asset checks and results are emitted to alerting, metrics, and OpenMetadata.

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

## Auto-Configuration

This package is **fully auto-configured**:

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
from phlo_quality.checks import null_check, uniqueness_check

@phlo_quality(
    asset="bronze.users",
    checks=[
        null_check(column="id"),
        uniqueness_check(column="email"),
    ]
)
def validate_users():
    pass
```

### CLI Commands

```bash
# Run quality checks
phlo quality run --asset bronze.users

# List available checks
phlo quality list
```

## Built-in Checks

| Check              | Description                         |
| ------------------ | ----------------------------------- |
| `null_check`       | Validates column has no NULL values |
| `uniqueness_check` | Validates column values are unique  |
| `range_check`      | Validates values are within range   |
| `regex_check`      | Validates values match pattern      |
| `freshness_check`  | Validates data is recent            |

## Entry Points

- `phlo.plugins.cli` - Provides `quality` CLI commands
- `phlo.plugins.quality` - Provides built-in check plugins
