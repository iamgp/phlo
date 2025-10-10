"""Great Expectations quality checks for Nightscout glucose data."""

from pathlib import Path

import great_expectations as gx
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)


GE_PROJECT_DIR = Path(__file__).parent.parent.parent / "great_expectations"
CHECKPOINT_NAME = "nightscout_glucose_checkpoint"


@asset_check(
    name="nightscout_glucose_quality",
    asset=AssetKey("processed_nightscout_entries"),
    blocking=True,
    description="Validate processed Nightscout glucose data using Great Expectations.",
)
def nightscout_glucose_quality_check(context) -> AssetCheckResult:
    if not GE_PROJECT_DIR.exists():
        context.log.error("Great Expectations project directory missing; failing check.")
        return AssetCheckResult(
            success=False,
            metadata={
                "reason": MetadataValue.text("ge_project_not_found"),
                "project_path": MetadataValue.path(str(GE_PROJECT_DIR)),
            },
        )

    try:
        ge_context = gx.get_context(context_root_dir=str(GE_PROJECT_DIR))
    except Exception as exc:  # pragma: no cover - configuration error
        context.log.error(f"Failed to load Great Expectations context: {exc}")
        return AssetCheckResult(
            success=False,
            metadata={"reason": MetadataValue.text("context_load_failed")},
        )

    try:
        checkpoint_result: CheckpointResult = ge_context.run_checkpoint(
            checkpoint_name=CHECKPOINT_NAME
        )
    except Exception as exc:  # pragma: no cover - checkpoint misconfiguration
        context.log.error(f"Checkpoint execution failed: {exc}")
        return AssetCheckResult(
            success=False,
            metadata={"reason": MetadataValue.text("checkpoint_execution_failed")},
        )

    expectation_results = []
    evaluated_rows = 0
    successful_expectations = 0
    evaluated_expectations = 0
    suite_names: set[str] = set()

    for run_result in checkpoint_result.run_results.values():
        validation_result: ExpectationSuiteValidationResult = run_result["validation_result"]
        suite_names.add(validation_result.meta.get("expectation_suite_name", "nightscout_glucose_suite"))

        stats = validation_result.statistics or {}
        evaluated_rows = max(evaluated_rows, stats.get("evaluated_row_count", 0))
        successful_expectations += stats.get("successful_expectations", 0)
        evaluated_expectations += stats.get("evaluated_expectations", 0)

        for result in validation_result.results:
            expectation_results.append(result.to_json_dict())

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
        "success_rate_percent": MetadataValue.float(success_rate),
        "checkpoint_succeeded": MetadataValue.bool(checkpoint_result.success),
        "suite_names": MetadataValue.json(sorted(suite_names)),
        "expectation_results": MetadataValue.json(expectation_results),
    }

    return AssetCheckResult(success=checkpoint_result.success, metadata=metadata)
