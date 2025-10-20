# nightscout.py - Quality checks for Nightscout glucose data using Pandera schema validation
# Implements data quality assurance for the silver layer, ensuring processed glucose readings
# conform to business rules, data types, and expected ranges

from __future__ import annotations

import pandas as pd
import pandera.errors
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check

from cascade.defs.resources.trino import TrinoResource
from cascade.schemas.glucose import (
FactGlucoseReadings,
get_fact_glucose_dagster_type,
)

# --- Query Templates ---
# SQL query templates for data validation
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
FROM iceberg.silver.fct_glucose_readings
"""


# --- Asset Checks ---
# Dagster asset checks for data quality validation
@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey(["fct_glucose_readings"]),
    blocking=False,
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
        query = (
            f"{FACT_QUERY_BASE}\n"
            f"WHERE DATE(reading_timestamp) = DATE '{partition_date}'"
        )
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            if not cursor.description:
                context.log.warning(
                    "Trino did not return column metadata for query, aborting check."
                )
                return AssetCheckResult(
                    passed=False,
                    metadata={
                        "reason": MetadataValue.text("missing_column_metadata"),
                        "query": MetadataValue.text(query),
                    },
                )

            columns = [desc[0] for desc in cursor.description]

        fact_df = pd.DataFrame(rows, columns=columns)

        # Explicitly cast columns to correct types (Trino client may return some as strings)
        type_conversions = {
            "glucose_mg_dl": "int64",
            "hour_of_day": "int64",
            "day_of_week": "int64",
            "is_in_range": "int64",
        }
        for col, dtype in type_conversions.items():
            if col in fact_df.columns:
                fact_df[col] = fact_df[col].astype(dtype)

        # Convert timestamp if it's not already datetime
        if "reading_timestamp" in fact_df.columns:
            fact_df["reading_timestamp"] = pd.to_datetime(fact_df["reading_timestamp"])

        context.log.info(
            "Loaded %d rows from iceberg.silver.fct_glucose_readings", len(fact_df)
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
                "query": MetadataValue.text(query),
            },
        )

    if fact_df.empty:
        context.log.warning("No rows returned for validation; marking check as skipped.")
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available for selected partition"),
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
                    + "\n".join(
                        [f"- **{col}**: {dtype}" for col, dtype in schema_info.items()]
                    )
                ),
                "dagster_type": MetadataValue.text(str(get_fact_glucose_dagster_type())),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(
            "Schema validation failed with %d check failures", len(failure_cases)
        )

        failures_by_column = failure_cases.groupby("column").size().to_dict()
        failures_by_check = failure_cases.groupby("check").size().to_dict()

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

    except Exception as exc:  # pragma: no cover - defensive logging
        context.log.exception(f"Unexpected error during validation: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("unexpected_error"),
                "error": MetadataValue.text(str(exc)),
            },
        )
