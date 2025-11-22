"""
Cascade Quality Framework

Declarative quality checks that reduce boilerplate by 70%.

## Quick Example

```python
from cascade.quality import cascade_quality, NullCheck, RangeCheck, FreshnessCheck

@cascade_quality(
    table="bronze.weather_observations",
    checks=[
        NullCheck(columns=["station_id", "temperature"]),
        RangeCheck(column="temperature", min_value=-50, max_value=60),
        FreshnessCheck(timestamp_column="observation_time", max_age_hours=2),
    ],
    group="weather",
    schedule="@hourly",
)
def weather_quality_check():
    """Quality checks for weather observations."""
    pass
```

## Available Quality Checks

- **NullCheck**: Verify no null values in specified columns
- **RangeCheck**: Verify numeric values are within specified range
- **FreshnessCheck**: Verify data recency (no stale data)
- **UniqueCheck**: Verify uniqueness constraints
- **CountCheck**: Verify row count meets expectations
- **SchemaCheck**: Verify Pandera schema compliance

## Comparison

### Before (30-40 lines):
```python
@asset_check(
    name="weather_quality",
    asset=AssetKey(["weather_observations"]),
    blocking=True,
    description="Validate weather data",
)
def weather_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    query = "SELECT * FROM bronze.weather_observations"
    # ... 20+ lines of boilerplate
    # ... type conversions
    # ... validation logic
    # ... error handling
    return AssetCheckResult(passed=True, metadata={...})
```

### After (5-10 lines):
```python
@cascade_quality(
    table="bronze.weather_observations",
    checks=[
        NullCheck(columns=["station_id", "temperature"]),
        RangeCheck(column="temperature", min_value=-50, max_value=60),
    ],
)
def weather_quality_check():
    pass
```

## Features

- ✅ 70% reduction in boilerplate code
- ✅ Type-safe quality check definitions
- ✅ Automatic Dagster asset check generation
- ✅ Rich metadata in MaterializeResult
- ✅ Composable quality checks
- ✅ Support for Trino and DuckDB backends
"""

from cascade.quality.checks import (
    CountCheck,
    FreshnessCheck,
    NullCheck,
    QualityCheck,
    RangeCheck,
    SchemaCheck,
    UniqueCheck,
)
from cascade.quality.decorator import cascade_quality

__all__ = [
    # Decorator
    "cascade_quality",
    # Base class
    "QualityCheck",
    # Quality checks
    "NullCheck",
    "RangeCheck",
    "FreshnessCheck",
    "UniqueCheck",
    "CountCheck",
    "SchemaCheck",
]

__version__ = "1.0.0"
