"""
Phlo Quality Framework.

Declarative quality checks that reduce boilerplate by 70%.

Usage::

    from phlo_quality import NullCheck, RangeCheck, phlo_quality

    @phlo_quality(
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
    - PatternCheck: Verify string values match regex patterns
"""

from phlo_quality.checks import (
    CountCheck,
    CustomSQLCheck,
    FreshnessCheck,
    NullCheck,
    PatternCheck,
    QualityCheck,
    RangeCheck,
    SchemaCheck,
    UniqueCheck,
)
from phlo_quality.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract, dbt_check_name
from phlo_quality.decorator import get_quality_checks, phlo_quality
from phlo_quality.reconciliation import AggregateConsistencyCheck, ReconciliationCheck

__all__ = [
    # Decorator (use as @phlo_quality(...))
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
    "PatternCheck",
    # Reconciliation checks
    "ReconciliationCheck",
    "AggregateConsistencyCheck",
    # Contract helpers
    "PANDERA_CONTRACT_CHECK_NAME",
    "QualityCheckContract",
    "dbt_check_name",
]

__version__ = "1.0.0"
