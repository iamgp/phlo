"""
Cascade Quality Framework.

Declarative quality checks that reduce boilerplate by 70%.

Quick Example::

    from phlo.quality import phlo_quality, NullCheck, RangeCheck

    @phlo_quality(
        table="bronze.weather_observations",
        checks=[
            NullCheck(columns=["station_id", "temperature"]),
            RangeCheck(column="temperature", min_value=-50, max_value=60),
        ],
    )
    def weather_quality_check():
        pass

Available Quality Checks:
    - NullCheck: Verify no null values in specified columns
    - RangeCheck: Verify numeric values are within specified range
    - FreshnessCheck: Verify data recency (no stale data)
    - UniqueCheck: Verify uniqueness constraints
    - CountCheck: Verify row count meets expectations
    - SchemaCheck: Verify Pandera schema compliance

See phlo.quality.examples for comprehensive usage examples.
"""

from phlo.quality.checks import (
    CountCheck,
    FreshnessCheck,
    NullCheck,
    QualityCheck,
    RangeCheck,
    SchemaCheck,
    UniqueCheck,
)
from phlo.quality.decorator import phlo_quality

__all__ = [
    # Decorator
    "phlo_quality",
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
