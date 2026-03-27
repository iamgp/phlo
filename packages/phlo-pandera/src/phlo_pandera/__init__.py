"""
Phlo Quality Framework.

Declarative quality checks that reduce boilerplate by 70%.

Usage::

    from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

    @phlo_pandera(
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

from phlo_pandera.checks import (
    CountCheck,
    FreshnessCheck,
    NullCheck,
    QualityCheck,
    RangeCheck,
    UniqueCheck,
)
from phlo_pandera.checks_extra import CustomSQLCheck, PatternCheck, SchemaCheck
from phlo_pandera.contract import PANDERA_CONTRACT_CHECK_NAME, QualityCheckContract, dbt_check_name
from phlo_pandera.decorator import clear_quality_checks, get_quality_checks, phlo_pandera
from phlo_pandera.schema_extractor import PanderaSchemaExtractor
from phlo_pandera.reconciliation import (
    AggregateConsistencyCheck,
    AggregateSpec,
    ChecksumReconciliationCheck,
    KeyParityCheck,
    MultiAggregateConsistencyCheck,
    ReconciliationCheck,
)

__all__ = [
    # Decorator (use as @phlo_pandera(...))
    "phlo_pandera",
    "get_quality_checks",
    "clear_quality_checks",
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
    "AggregateSpec",
    "KeyParityCheck",
    "MultiAggregateConsistencyCheck",
    "ChecksumReconciliationCheck",
    # Schema extraction
    "PanderaSchemaExtractor",
    # Contract helpers
    "PANDERA_CONTRACT_CHECK_NAME",
    "QualityCheckContract",
    "dbt_check_name",
]

__version__ = "0.2.2"
