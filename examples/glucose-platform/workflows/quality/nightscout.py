"""Quality checks for Nightscout glucose data using Pandera schema validation.

Implements data quality assurance for the silver and gold layers, ensuring processed
glucose readings conform to business rules, data types, and expected ranges.

This module demonstrates two approaches to quality checks:
1. Traditional @asset_check with Pandera schemas (nightscout_glucose_quality_check)
2. @phlo_quality decorator for declarative checks (glucose_readings_quality)
"""

from __future__ import annotations

import pandas as pd
import pandera.errors
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from phlo_trino.resource import TrinoResource

from workflows.schemas.nightscout import FactDailyGlucoseMetrics, FactGlucoseReadings

# Import quality check types for @phlo_quality decorator
try:
    from phlo_quality import FreshnessCheck, NullCheck, RangeCheck, phlo_quality

    PHLO_QUALITY_AVAILABLE = True
except ImportError:
    PHLO_QUALITY_AVAILABLE = False


# ---------------------------------------------------------------------------
# @phlo_quality decorator approach (declarative, reduces boilerplate by 70-80%)
# ---------------------------------------------------------------------------
if PHLO_QUALITY_AVAILABLE:
    from phlo_quality import CountCheck, UniqueCheck

    @phlo_quality(
        table="silver.fct_glucose_readings",
        checks=[
            NullCheck(columns=["entry_id", "glucose_mg_dl", "reading_timestamp"]),
            UniqueCheck(columns=["entry_id"]),
            RangeCheck(column="glucose_mg_dl", min_value=20, max_value=600),
            RangeCheck(column="hour_of_day", min_value=0, max_value=23),
            FreshnessCheck(timestamp_column="reading_timestamp", max_age_hours=24),
            CountCheck(min_rows=1),
        ],
        group="nightscout",
        blocking=True,
    )
    def glucose_readings_quality():
        """Declarative quality checks for glucose readings using @phlo_quality."""
        pass

    @phlo_quality(
        table="gold.fct_daily_glucose_metrics",
        checks=[
            NullCheck(columns=["reading_date", "reading_count", "avg_glucose_mg_dl"]),
            UniqueCheck(columns=["reading_date"]),
            RangeCheck(column="avg_glucose_mg_dl", min_value=20, max_value=600),
            RangeCheck(column="time_in_range_pct", min_value=0, max_value=100),
            CountCheck(min_rows=1),
        ],
        group="nightscout",
        blocking=True,
    )
    def daily_metrics_quality():
        """Declarative quality checks for daily glucose metrics."""
        pass


# ---------------------------------------------------------------------------
# Traditional @asset_check approach (more control, custom logic)
# ---------------------------------------------------------------------------

FACT_QUERY_BASE = """
SELECT
    entry_id,
    glucose_mg_dl,
    reading_timestamp,
    direction,
    hour_of_day,
    day_of_week,
    glucose_category,
    is_in_range
FROM iceberg_dev.silver.fct_glucose_readings
"""


@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=True,
    description="Validate processed Nightscout glucose data using Pandera schema validation.",
)
def nightscout_glucose_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check using Pandera for type-safe schema validation.

    Validates glucose readings against the FactGlucoseReadings schema,
    checking data types, ranges, and business rules directly against Iceberg via Trino.
    """
    query = FACT_QUERY_BASE
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = f"{FACT_QUERY_BASE}\nWHERE DATE(reading_timestamp) = DATE '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            if not cursor.description:
                context.log.warning("Trino did not return column metadata")
                return AssetCheckResult(
                    passed=False,
                    metadata={"reason": MetadataValue.text("missing_column_metadata")},
                )

            columns = [desc[0] for desc in cursor.description]

        fact_df = pd.DataFrame(rows, columns=columns)

        type_conversions = {
            "glucose_mg_dl": "int64",
            "hour_of_day": "int64",
            "day_of_week": "int64",
            "is_in_range": "int64",
        }
        for col, dtype in type_conversions.items():
            if col in fact_df.columns:
                fact_df[col] = fact_df[col].astype(dtype)

        if "reading_timestamp" in fact_df.columns:
            fact_df["reading_timestamp"] = pd.to_datetime(fact_df["reading_timestamp"])

        context.log.info(f"Loaded {len(fact_df)} rows for validation")

    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
            },
        )

    if fact_df.empty:
        context.log.warning("No rows returned for validation")
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available for selected partition"),
            },
        )

    context.log.info("Validating data with Pandera schema...")
    try:
        FactGlucoseReadings.validate(fact_df, lazy=True)
        context.log.info("All validation checks passed!")

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(fact_df)),
                "columns_validated": MetadataValue.int(len(fact_df.columns)),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Validation failed with {len(failure_cases)} check failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(fact_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(
                    failure_cases.groupby("column").size().to_dict()
                ),
                "sample_failures": MetadataValue.json(
                    failure_cases.head(10).to_dict(orient="records")
                ),
            },
        )


DAILY_METRICS_QUERY = """
SELECT
    reading_date,
    day_name,
    day_of_week,
    week_of_year,
    month,
    year,
    reading_count,
    avg_glucose_mg_dl,
    min_glucose_mg_dl,
    max_glucose_mg_dl,
    stddev_glucose_mg_dl,
    time_in_range_pct,
    time_below_range_pct,
    time_above_range_pct,
    estimated_a1c_pct
FROM iceberg_dev.gold.fct_daily_glucose_metrics
"""


@asset_check(
    name="daily_glucose_metrics_quality",
    asset=AssetKey(["fct_daily_glucose_metrics"]),
    blocking=True,
    description="Validate daily glucose metrics using Pandera schema validation.",
)
def daily_glucose_metrics_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check for daily glucose metrics fact table.

    Validates aggregated daily glucose metrics against the FactDailyGlucoseMetrics schema.
    """
    query = DAILY_METRICS_QUERY
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = f"{DAILY_METRICS_QUERY}\nWHERE reading_date = DATE '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with trino.cursor(schema="gold") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            if not cursor.description:
                return AssetCheckResult(
                    passed=False,
                    metadata={"reason": MetadataValue.text("missing_column_metadata")},
                )

            columns = [desc[0] for desc in cursor.description]

        metrics_df = pd.DataFrame(rows, columns=columns)

        type_conversions = {
            "day_of_week": "int64",
            "week_of_year": "int64",
            "month": "int64",
            "year": "int64",
            "reading_count": "int64",
        }
        for col, dtype in type_conversions.items():
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].astype(dtype)

        if "reading_date" in metrics_df.columns:
            metrics_df["reading_date"] = pd.to_datetime(metrics_df["reading_date"])

        context.log.info(f"Loaded {len(metrics_df)} rows for validation")

    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
            },
        )

    if metrics_df.empty:
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available"),
            },
        )

    context.log.info("Validating daily metrics with Pandera schema...")
    try:
        FactDailyGlucoseMetrics.validate(metrics_df, lazy=True)
        context.log.info("All validation checks passed!")

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(metrics_df)),
                "columns_validated": MetadataValue.int(len(metrics_df.columns)),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Validation failed with {len(failure_cases)} failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(metrics_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(
                    failure_cases.groupby("column").size().to_dict()
                ),
            },
        )
