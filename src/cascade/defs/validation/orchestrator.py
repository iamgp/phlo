"""
Validation Orchestrator Asset.

This module provides the main validation orchestrator asset that coordinates
all validation gates (Pandera, dbt, freshness, schema compatibility) and
aggregates results before branch promotion.
"""

from datetime import datetime

import dagster as dg
from cascade.config import config
from cascade.defs.validation.dbt_validator import DBTValidatorResource
from cascade.defs.validation.freshness_validator import FreshnessValidatorResource
from cascade.defs.validation.pandera_validator import PanderaValidatorResource
from cascade.defs.validation.schema_validator import SchemaCompatibilityValidatorResource


@dg.asset(
    deps=[
        dg.AssetKey(["fct_glucose_readings"]),
        dg.AssetKey(["fct_daily_glucose_metrics"]),
        dg.AssetKey(["fct_github_user_events"]),
        dg.AssetKey(["fct_github_repo_stats"]),
    ],
    retry_policy=dg.RetryPolicy(
        max_retries=config.validation_retry_max_attempts,
        delay=config.validation_retry_delay_seconds
    ),
    group_name="validation",
    description="Orchestrates all validation gates before branch promotion"
)
def validation_orchestrator(
    context: dg.AssetExecutionContext,
    pandera_validator: PanderaValidatorResource,
    dbt_validator: DBTValidatorResource,
    freshness_validator: FreshnessValidatorResource,
    schema_validator: SchemaCompatibilityValidatorResource,
) -> dg.MaterializeResult:
    """
    Runs all validation gates and aggregates results.

    Supports automatic retry with detailed logging.

    Validation Gates:
    1. Pandera schema validation (severity-based blocking)
    2. dbt test execution (all tests must pass)
    3. Data freshness checks (configurable blocking)
    4. Schema compatibility (allow additive, block breaking)

    Returns:
        MaterializeResult with metadata containing:
        - all_passed: bool
        - branch_name: str
        - validation results for each gate
        - blocking_failures: list of failures that block promotion
        - warnings: list of non-blocking warnings
        - retry_attempt: int
    """
    # Get branch name from run config
    branch_name = context.run_config.get("branch_name", "main")
    retry_attempt = context.retry_number

    context.log.info(
        f"Running validation orchestrator on branch {branch_name} "
        f"(attempt {retry_attempt + 1}/{config.validation_retry_max_attempts})"
    )

    # Run all validators
    context.log.info("Running Pandera schema validation...")
    pandera_results = pandera_validator.validate_all_tables(branch_name)

    context.log.info("Running dbt tests...")
    dbt_results = dbt_validator.run_tests(branch_name)

    context.log.info("Checking data freshness...")
    freshness_results = freshness_validator.check_freshness(context)

    context.log.info("Validating schema compatibility...")
    schema_results = schema_validator.check_compatibility(branch_name, "main")

    # Aggregate results
    all_passed = all([
        pandera_results["all_passed"],
        dbt_results["all_passed"],
        freshness_results["all_fresh"] or not config.freshness_blocks_promotion,
        schema_results["compatible"]
    ])

    blocking_failures = []
    warnings = []

    # Collect Pandera failures
    if not pandera_results["all_passed"]:
        for failure in pandera_results["critical_failures"]:
            blocking_failures.append(
                f"Pandera: {failure['table']}.{failure['column']} - {failure['check']}"
            )
    if pandera_results.get("warnings"):
        for warning in pandera_results["warnings"]:
            warnings.append(
                f"Pandera: {warning['table']}.{warning['column']} - {warning['check']}"
            )

    # Collect dbt failures
    if not dbt_results["all_passed"]:
        for failure in dbt_results["failures"]:
            blocking_failures.append(
                f"dbt: {failure['test_name']} ({failure.get('failed_rows', 0)} rows failed)"
            )

    # Collect freshness violations
    if not freshness_results["all_fresh"]:
        for violation in freshness_results["violations"]:
            message = (
                f"Freshness: {violation['asset']} is {violation['age_hours']}h old "
                f"(threshold: {violation['threshold_hours']}h)"
            )
            if config.freshness_blocks_promotion:
                blocking_failures.append(message)
            else:
                warnings.append(message)

    # Collect schema compatibility issues
    if not schema_results["compatible"]:
        for change in schema_results["breaking_changes"]:
            blocking_failures.append(
                f"Schema: {change['table']} - {change['change_type']}: {change['details']}"
            )
    if schema_results.get("additive_changes"):
        for change in schema_results["additive_changes"]:
            warnings.append(
                f"Schema: {change['table']} - {change['change_type']}: {change['details']}"
            )

    # Log results
    if all_passed:
        context.log.info(
            f"All validations passed for branch {branch_name}! "
            f"({pandera_results['tables_validated']} Pandera checks, "
            f"{dbt_results['tests_run']} dbt tests, "
            f"{len(schema_results['tables_checked'])} schema checks)"
        )
    else:
        context.log.error(
            f"Validation failures for branch {branch_name}:\n" +
            "\n".join(f"  - {f}" for f in blocking_failures)
        )
        if config.validation_retry_enabled and retry_attempt < config.validation_retry_max_attempts - 1:
            context.log.warning(
                f"Will retry validation (attempt {retry_attempt + 2}/{config.validation_retry_max_attempts})"
            )

    # Log warnings
    if warnings:
        context.log.warning(
            f"Non-blocking warnings for branch {branch_name}:\n" +
            "\n".join(f"  - {w}" for w in warnings)
        )

    return dg.MaterializeResult(
        metadata={
            "all_passed": all_passed,
            "branch_name": branch_name,
            "pandera_results": pandera_results,
            "dbt_results": dbt_results,
            "freshness_results": freshness_results,
            "schema_results": schema_results,
            "blocking_failures": blocking_failures,
            "warnings": warnings,
            "retry_attempt": retry_attempt,
            "validated_at": datetime.now().isoformat()
        }
    )
