"""
Phlo Quality Framework.

Declarative quality checks that reduce boilerplate by 70%.

Usage::

    import phlo
    from phlo.quality import NullCheck, RangeCheck

    @phlo.quality(
        table="bronze.weather_observations",
        checks=[
            NullCheck(columns=["station_id", "temperature"]),
            RangeCheck(column="temperature", min_value=-50, max_value=60),
        ],
    )
    def weather_quality():
        pass

Available Checks:
    - NullCheck: Verify no null values in specified columns
    - RangeCheck: Verify numeric values within range
    - FreshnessCheck: Verify data recency
    - UniqueCheck: Verify uniqueness constraints
    - CountCheck: Verify row count bounds
    - SchemaCheck: Verify Pandera schema compliance
    - CustomSQLCheck: Execute arbitrary SQL assertions
"""

from phlo.quality.checks import (
    CountCheck,
    CustomSQLCheck,
    FreshnessCheck,
    NullCheck,
    QualityCheck,
    RangeCheck,
    SchemaCheck,
    UniqueCheck,
)
from phlo.quality.decorator import phlo_quality, get_quality_checks

__all__ = [
    # Decorator (use as @phlo.quality(...) after `import phlo`)
    "phlo_quality",
    "get_quality_checks",
    # Base class
    "QualityCheck",
    # Quality checks
    "NullCheck",
    "RangeCheck",
    "FreshnessCheck",
    "UniqueCheck",
    "CountCheck",
    "SchemaCheck",
    "CustomSQLCheck",
]

__version__ = "1.0.0"
