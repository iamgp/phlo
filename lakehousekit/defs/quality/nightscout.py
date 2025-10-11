from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import great_expectations as gx
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)


GE_PROJECT_DIR = Path("/great_expectations")
CHECKPOINT_NAME = "nightscout_glucose_checkpoint"
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
    blocking=True,
    description="Validate processed Nightscout glucose data using Great Expectations.",
)
def nightscout_glucose_quality_check(context) -> AssetCheckResult:
    try:
        if not GE_PROJECT_DIR.exists():
            context.log.error("Great Expectations project directory missing; failing check.")
            return AssetCheckResult(
                passed=False,
                metadata={
                    "reason": MetadataValue.text("ge_project_not_found"),
                    "project_path": MetadataValue.path(str(GE_PROJECT_DIR)),
                },
            )

        try:
            ge_context = gx.get_context(context_root_dir=str(GE_PROJECT_DIR))
        except Exception as exc:
            context.log.error(f"Failed to load Great Expectations context: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={"reason": MetadataValue.text("context_load_failed")},
            )

        try:
            with duckdb.connect(database=str(DUCKDB_PATH), read_only=True) as conn:
                fact_df = conn.execute(FACT_QUERY).df()
        except Exception as exc:
            context.log.error(f"Failed to load fact_glucose_readings from DuckDB: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={"reason": MetadataValue.text("duckdb_query_failed")},
            )

        validations = [
            {
                "batch_request": {
                    "datasource_name": "warehouse.main_curated.fact_glucose_readings",
                    "data_connector_name": "default_runtime_connector",
                    "data_asset_name": "fact_glucose_readings",
                    "runtime_parameters": {"batch_data": fact_df},
                    "batch_identifiers": {"default_identifier_name": "fact_glucose_readings"},
                },
                "expectation_suite_name": "nightscout_glucose_suite",
            }
        ]

        try:
            checkpoint_result: CheckpointResult = ge_context.run_checkpoint(
                checkpoint_name=CHECKPOINT_NAME,
                validations=validations,
            )
        except Exception as exc:
            context.log.error(f"Checkpoint execution failed: {exc}")
            return AssetCheckResult(
                passed=False,
                metadata={"reason": MetadataValue.text("checkpoint_execution_failed")},
            )

        expectation_results = []
        evaluated_rows = 0
        successful_expectations = 0
        evaluated_expectations = 0
        suite_names: set[str] = set()

        for run_result in checkpoint_result.run_results.values():
            validation_result: ExpectationSuiteValidationResult = run_result["validation_result"]
            suite_names.add(
                validation_result.meta.get("expectation_suite_name", "nightscout_glucose_suite")
            )

            stats = validation_result.statistics or {}
            evaluated_rows = max(
                evaluated_rows, int(stats.get("evaluated_row_count", 0) or 0)
            )
            successful_expectations += int(stats.get("successful_expectations", 0) or 0)
            evaluated_expectations += int(stats.get("evaluated_expectations", 0) or 0)

            for result in validation_result.results:
                expectation_results.append(_sanitize_json(result.to_json_dict()))

        failed_expectations = max(evaluated_expectations - successful_expectations, 0)
        success_rate = (
            (successful_expectations / evaluated_expectations) * 100.0
            if evaluated_expectations
            else 0.0
        )

        metadata = {
            "rows_evaluated": MetadataValue.int(evaluated_rows),
            "expectations_passed": MetadataValue.int(successful_expectations),
            "expectations_failed": MetadataValue.int(failed_expectations),
            "success_rate_percent": MetadataValue.float(float(success_rate)),
            "checkpoint_succeeded": MetadataValue.bool(bool(checkpoint_result.success)),
            "suite_names": MetadataValue.json(sorted(suite_names)),
            "expectation_results": MetadataValue.json(expectation_results),
        }

        return AssetCheckResult(passed=checkpoint_result.success, metadata=metadata)

    except Exception:
        context.log.exception(
            "nightscout_glucose_quality_check encountered an unexpected error"
        )
        raise

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
