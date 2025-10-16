from __future__ import annotations

import pandera.errors
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check

from cascade.defs.resources import DuckLakeResource
from cascade.schemas.glucose import (
    FactGlucoseReadings,
    get_fact_glucose_dagster_type,
)

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
FROM main_curated.fact_glucose_readings
"""


@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fact_glucose_readings"]),
    blocking=True,
    description="Validate processed Nightscout glucose data using Pandera schema validation.",
)
def nightscout_glucose_quality_check(context, duckdb: DuckLakeResource) -> AssetCheckResult:
    """
    Quality check using Pandera for type-safe schema validation.

    Validates glucose readings against the FactGlucoseReadings schema,
    checking data types, ranges, and business rules.
    """
    # Build query with partition filter if applicable
    query = FACT_QUERY_BASE
    if context.has_partition_key:
        partition_date = context.partition_key
        query = f"{FACT_QUERY_BASE}\nWHERE DATE(reading_timestamp) = '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with duckdb.get_connection() as conn:
            table_exists = conn.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'main_curated'
                  AND table_name = 'fact_glucose_readings'
                LIMIT 1
                """
            ).fetchone()

            if not table_exists:
                context.log.warning(
                    "DuckLake table main_curated.fact_glucose_readings not found; "
                    "skipping quality check."
                )
                return AssetCheckResult(
                    passed=True,
                    metadata={
                        "reason": MetadataValue.text("ducklake_table_missing"),
                        "note": MetadataValue.text(
                            "Table is created after the first successful transform run."
                        ),
                    },
                )

            context.log.info("Loading data from DuckLake...")
            fact_df = conn.execute(query).df()
        context.log.info(f"Loaded {len(fact_df)} rows from fact_glucose_readings")
    except Exception as exc:
        context.log.error(f"Failed to load data from DuckLake: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("ducklake_query_failed"),
                "error": MetadataValue.text(str(exc)),
            },
        )

    # Validate using Pandera schema
    context.log.info("Validating data with Pandera schema...")
    try:
        # Use lazy validation to collect all errors
        FactGlucoseReadings.validate(fact_df, lazy=True)

        context.log.info("All validation checks passed!")

        # Build schema metadata for UI display
        schema_info = {
            "entry_id": "str (unique, non-null)",
            "glucose_mg_dl": "int (20-600 mg/dL, non-null)",
            "reading_timestamp": "datetime (non-null)",
            "direction": (
                "str (Flat/FortyFiveUp/FortyFiveDown/SingleUp/"
                "SingleDown/DoubleUp/DoubleDown/NONE, nullable)"
            ),
            "hour_of_day": "int (0-23, non-null)",
            "day_of_week": "int (0-6, non-null)",
            "glucose_category": (
                "str (hypoglycemia/in_range/hyperglycemia_mild/hyperglycemia_severe, non-null)"
            ),
            "is_in_range": "int (0 or 1, non-null)",
        }

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(fact_df)),
                "columns_validated": MetadataValue.int(len(fact_df.columns)),
                "schema_version": MetadataValue.text("1.0.0"),
                "pandera_schema": MetadataValue.md(
                    "## Validated Schema\n\n"
                    + "\n".join([f"- **{col}**: {dtype}" for col, dtype in schema_info.items()])
                ),
                "dagster_type": MetadataValue.text(str(get_fact_glucose_dagster_type())),
            },
        )

    except pandera.errors.SchemaErrors as err:
        # Extract failure information
        failure_cases = err.failure_cases

        context.log.warning(f"Schema validation failed with {len(failure_cases)} check failures")

        # Group failures by column and check type for better reporting
        failures_by_column = failure_cases.groupby("column").size().to_dict()
        failures_by_check = failure_cases.groupby("check").size().to_dict()

        # Get sample of failing rows (up to 20)
        sample_failures = failure_cases.head(20)[
            ["schema_context", "column", "check", "check_number", "failure_case"]
        ].to_dict(orient="records")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(fact_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(failures_by_column),
                "failures_by_check": MetadataValue.json(failures_by_check),
                "sample_failures": MetadataValue.json(sample_failures),
                "error_summary": MetadataValue.text(str(err)),
            },
        )

    except Exception as exc:
        context.log.exception(f"Unexpected error during validation: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("unexpected_error"),
                "error": MetadataValue.text(str(exc)),
            },
        )
