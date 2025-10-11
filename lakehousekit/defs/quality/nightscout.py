from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from great_expectations.core import ExpectationSuite
from great_expectations.data_context import EphemeralDataContext
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)


DUCKDB_PATH = Path("/data/duckdb/warehouse.duckdb")
FACT_QUERY = """
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
    blocking=False,
    description="Validate processed Nightscout glucose data using Great Expectations.",
)
def nightscout_glucose_quality_check(context) -> AssetCheckResult:
    """
    Quality check using Great Expectations with in-memory context.

    This avoids file-based context loading issues and uses an ephemeral
    data context that won't cause subprocess crashes.
    """
    try:
        # Check if DuckDB file exists first
        if not DUCKDB_PATH.exists():
            context.log.warning("DuckDB file does not exist yet; skipping quality check.")
            return AssetCheckResult(
                passed=True,
                metadata={
                    "reason": MetadataValue.text("duckdb_not_found_skipped"),
                    "note": MetadataValue.text("This is expected on first run before data is loaded"),
                },
            )

        # Load data from DuckDB
        context.log.info("Loading data from DuckDB...")
        try:
            with duckdb.connect(database=str(DUCKDB_PATH), read_only=True) as conn:
                fact_df = conn.execute(FACT_QUERY).df()
            context.log.info(f"Loaded {len(fact_df)} rows from fact_glucose_readings")
        except Exception as exc:
            context.log.error(f"Failed to load data from DuckDB: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "reason": MetadataValue.text("duckdb_query_failed"),
                    "error": MetadataValue.text(str(exc)),
                },
            )

        # Create ephemeral GE context (in-memory, no file I/O)
        context.log.info("Creating ephemeral Great Expectations context...")
        try:
            project_config = DataContextConfig(
                store_backend_defaults=InMemoryStoreBackendDefaults()
            )
            ge_context = EphemeralDataContext(project_config=project_config)
            context.log.info("GE context created successfully")
        except Exception as exc:
            context.log.error(f"Failed to create GE context: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "reason": MetadataValue.text("context_creation_failed"),
                    "error": MetadataValue.text(str(exc)),
                },
            )

        # Get validator for the dataframe
        context.log.info("Creating GE validator...")
        try:
            validator = ge_context.sources.add_pandas("fact_glucose_readings").read_dataframe(fact_df)
            context.log.info("Validator created successfully")
        except Exception as exc:
            context.log.error(f"Failed to create validator: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "reason": MetadataValue.text("validator_creation_failed"),
                    "error": MetadataValue.text(str(exc)),
                },
            )

        # Define expectations (you can customize these)
        context.log.info("Running expectations...")
        expectations = []

        try:
            # Check for null values in key columns
            expectations.append(
                validator.expect_column_values_to_not_be_null(column="entry_id")
            )
            expectations.append(
                validator.expect_column_values_to_not_be_null(column="glucose_mg_dl")
            )
            expectations.append(
                validator.expect_column_values_to_not_be_null(column="reading_timestamp")
            )

            # Check glucose values are in reasonable range (20-600 mg/dL)
            expectations.append(
                validator.expect_column_values_to_be_between(
                    column="glucose_mg_dl",
                    min_value=20,
                    max_value=600
                )
            )

            # Check direction is valid
            expectations.append(
                validator.expect_column_values_to_be_in_set(
                    column="direction",
                    value_set=["Flat", "FortyFiveUp", "FortyFiveDown", "SingleUp", "SingleDown", "DoubleUp", "DoubleDown", "NONE", None]
                )
            )

            # Check is_in_range is boolean
            expectations.append(
                validator.expect_column_values_to_be_in_set(
                    column="is_in_range",
                    value_set=[True, False, 0, 1]
                )
            )

            context.log.info(f"Ran {len(expectations)} expectations")

        except Exception as exc:
            context.log.error(f"Failed to run expectations: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "reason": MetadataValue.text("expectations_execution_failed"),
                    "error": MetadataValue.text(str(exc)),
                },
            )

        # Aggregate results
        successful = sum(1 for exp in expectations if exp.success)
        failed = len(expectations) - successful
        success_rate = (successful / len(expectations)) * 100 if expectations else 0

        # Extract failed expectation details
        failed_expectations = [
            {
                "expectation_type": exp.expectation_config.expectation_type,
                "column": exp.expectation_config.kwargs.get("column"),
                "unexpected_count": exp.result.get("unexpected_count", 0),
            }
            for exp in expectations
            if not exp.success
        ]

        metadata = {
            "rows_evaluated": MetadataValue.int(len(fact_df)),
            "expectations_passed": MetadataValue.int(successful),
            "expectations_failed": MetadataValue.int(failed),
            "success_rate_percent": MetadataValue.float(float(success_rate)),
            "failed_expectations": MetadataValue.json(failed_expectations) if failed_expectations else MetadataValue.text("None"),
        }

        passed = failed == 0
        return AssetCheckResult(passed=passed, metadata=metadata)

    except Exception as exc:
        context.log.exception(
            f"nightscout_glucose_quality_check encountered an unexpected error: {exc}"
        )
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("unexpected_error"),
                "error": MetadataValue.text(str(exc)),
            },
        )

def _sanitize_json(value):
    if isinstance(value, dict):
        return {k: _sanitize_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        try:
            return value.tolist()
        except Exception:
            pass
    if isinstance(value, (float, int, bool)) or value is None:
        return value
    return json.loads(json.dumps(value, default=_numpy_default))


def _numpy_default(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
