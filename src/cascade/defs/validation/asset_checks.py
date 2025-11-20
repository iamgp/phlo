"""
Asset Checks for Data Quality Validation.

This module provides Dagster asset checks that validate data quality for all fact tables.
Each fact table has four checks:
1. Pandera schema validation
2. dbt tests
3. Data freshness
4. Schema compatibility with main branch

Checks are attached to the assets they validate and run automatically when assets materialize.
"""

import dagster as dg
from cascade.config import config
from cascade.defs.validation.pandera_validator import PanderaValidatorResource
from cascade.defs.validation.dbt_validator import DBTValidatorResource
from cascade.defs.validation.freshness_validator import FreshnessValidatorResource
from cascade.defs.validation.schema_validator import SchemaCompatibilityValidatorResource
from cascade.schemas.glucose import FactGlucoseReadings, FactDailyGlucoseMetrics
from cascade.schemas.github import FactGitHubUserEvents, FactGitHubRepoStats


# ============================================================================
# Glucose Readings Checks
# ============================================================================

@dg.asset_check(asset="fct_glucose_readings", blocking=True)
def pandera_check_glucose_readings(
    context,
    pandera_validator: PanderaValidatorResource
) -> dg.AssetCheckResult:
    """Validate glucose readings against Pandera schema."""
    branch = context.run.tags.get("branch", "main")
    result = pandera_validator.validate_table(
        "fct_glucose_readings",
        FactGlucoseReadings,
        branch
    )

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "critical_failures": result.get("critical_failures", []),
            "warnings": result.get("warnings", [])
        }
    )


@dg.asset_check(asset="fct_glucose_readings", blocking=True)
def dbt_tests_glucose_readings(
    context,
    dbt_validator: DBTValidatorResource
) -> dg.AssetCheckResult:
    """Run dbt tests for glucose readings model."""
    branch = context.run.tags.get("branch", "main")
    result = dbt_validator.run_tests_for_model("fct_glucose_readings", branch)

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "tests_run": result["tests_run"],
            "passed": result["passed"],
            "failed": result["failed"],
            "failures": result.get("failures", [])
        }
    )


@dg.asset_check(asset="fct_glucose_readings", blocking=False)
def freshness_check_glucose_readings(
    context,
    freshness_validator: FreshnessValidatorResource
) -> dg.AssetCheckResult:
    """Check freshness of glucose data."""
    result = freshness_validator.check_asset_freshness(context, "dlt_glucose_entries")

    severity = (
        dg.AssetCheckSeverity.ERROR
        if config.freshness_blocks_promotion
        else dg.AssetCheckSeverity.WARN
    )

    return dg.AssetCheckResult(
        passed=result["fresh"],
        severity=severity,
        metadata={
            "age_hours": result.get("age_hours"),
            "threshold_hours": result["threshold_hours"],
            "last_updated": result.get("last_updated")
        }
    )


@dg.asset_check(asset="fct_glucose_readings", blocking=True)
def schema_compatibility_glucose_readings(
    context,
    schema_validator: SchemaCompatibilityValidatorResource
) -> dg.AssetCheckResult:
    """Validate schema compatibility with main branch."""
    branch = context.run.tags.get("branch", "main")

    if branch == "main":
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={"note": "Already on main branch"}
        )

    result = schema_validator.check_table_compatibility(
        "silver.fct_glucose_readings",
        branch,
        "main"
    )

    return dg.AssetCheckResult(
        passed=result["compatible"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "breaking_changes": result.get("breaking_changes", []),
            "additive_changes": result.get("additive_changes", [])
        }
    )


# ============================================================================
# Daily Glucose Metrics Checks
# ============================================================================

@dg.asset_check(asset="fct_daily_glucose_metrics", blocking=True)
def pandera_check_daily_glucose_metrics(
    context,
    pandera_validator: PanderaValidatorResource
) -> dg.AssetCheckResult:
    """Validate daily glucose metrics against Pandera schema."""
    branch = context.run.tags.get("branch", "main")
    result = pandera_validator.validate_table(
        "fct_daily_glucose_metrics",
        FactDailyGlucoseMetrics,
        branch
    )

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "critical_failures": result.get("critical_failures", []),
            "warnings": result.get("warnings", [])
        }
    )


@dg.asset_check(asset="fct_daily_glucose_metrics", blocking=True)
def dbt_tests_daily_glucose_metrics(
    context,
    dbt_validator: DBTValidatorResource
) -> dg.AssetCheckResult:
    """Run dbt tests for daily glucose metrics model."""
    branch = context.run.tags.get("branch", "main")
    result = dbt_validator.run_tests_for_model("fct_daily_glucose_metrics", branch)

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "tests_run": result["tests_run"],
            "passed": result["passed"],
            "failed": result["failed"],
            "failures": result.get("failures", [])
        }
    )


@dg.asset_check(asset="fct_daily_glucose_metrics", blocking=False)
def freshness_check_daily_glucose_metrics(
    context,
    freshness_validator: FreshnessValidatorResource
) -> dg.AssetCheckResult:
    """Check freshness of glucose data (same source as readings)."""
    result = freshness_validator.check_asset_freshness(context, "dlt_glucose_entries")

    severity = (
        dg.AssetCheckSeverity.ERROR
        if config.freshness_blocks_promotion
        else dg.AssetCheckSeverity.WARN
    )

    return dg.AssetCheckResult(
        passed=result["fresh"],
        severity=severity,
        metadata={
            "age_hours": result.get("age_hours"),
            "threshold_hours": result["threshold_hours"],
            "last_updated": result.get("last_updated")
        }
    )


@dg.asset_check(asset="fct_daily_glucose_metrics", blocking=True)
def schema_compatibility_daily_glucose_metrics(
    context,
    schema_validator: SchemaCompatibilityValidatorResource
) -> dg.AssetCheckResult:
    """Validate schema compatibility with main branch."""
    branch = context.run.tags.get("branch", "main")

    if branch == "main":
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={"note": "Already on main branch"}
        )

    result = schema_validator.check_table_compatibility(
        "silver.fct_daily_glucose_metrics",
        branch,
        "main"
    )

    return dg.AssetCheckResult(
        passed=result["compatible"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "breaking_changes": result.get("breaking_changes", []),
            "additive_changes": result.get("additive_changes", [])
        }
    )


# ============================================================================
# GitHub User Events Checks
# ============================================================================

@dg.asset_check(asset="fct_github_user_events", blocking=True)
def pandera_check_github_user_events(
    context,
    pandera_validator: PanderaValidatorResource
) -> dg.AssetCheckResult:
    """Validate GitHub user events against Pandera schema."""
    branch = context.run.tags.get("branch", "main")
    result = pandera_validator.validate_table(
        "fct_github_user_events",
        FactGitHubUserEvents,
        branch
    )

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "critical_failures": result.get("critical_failures", []),
            "warnings": result.get("warnings", [])
        }
    )


@dg.asset_check(asset="fct_github_user_events", blocking=True)
def dbt_tests_github_user_events(
    context,
    dbt_validator: DBTValidatorResource
) -> dg.AssetCheckResult:
    """Run dbt tests for GitHub user events model."""
    branch = context.run.tags.get("branch", "main")
    result = dbt_validator.run_tests_for_model("fct_github_user_events", branch)

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "tests_run": result["tests_run"],
            "passed": result["passed"],
            "failed": result["failed"],
            "failures": result.get("failures", [])
        }
    )


@dg.asset_check(asset="fct_github_user_events", blocking=False)
def freshness_check_github_user_events(
    context,
    freshness_validator: FreshnessValidatorResource
) -> dg.AssetCheckResult:
    """Check freshness of GitHub user events data."""
    result = freshness_validator.check_asset_freshness(context, "dlt_github_user_events")

    severity = (
        dg.AssetCheckSeverity.ERROR
        if config.freshness_blocks_promotion
        else dg.AssetCheckSeverity.WARN
    )

    return dg.AssetCheckResult(
        passed=result["fresh"],
        severity=severity,
        metadata={
            "age_hours": result.get("age_hours"),
            "threshold_hours": result["threshold_hours"],
            "last_updated": result.get("last_updated")
        }
    )


@dg.asset_check(asset="fct_github_user_events", blocking=True)
def schema_compatibility_github_user_events(
    context,
    schema_validator: SchemaCompatibilityValidatorResource
) -> dg.AssetCheckResult:
    """Validate schema compatibility with main branch."""
    branch = context.run.tags.get("branch", "main")

    if branch == "main":
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={"note": "Already on main branch"}
        )

    result = schema_validator.check_table_compatibility(
        "silver.fct_github_user_events",
        branch,
        "main"
    )

    return dg.AssetCheckResult(
        passed=result["compatible"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "breaking_changes": result.get("breaking_changes", []),
            "additive_changes": result.get("additive_changes", [])
        }
    )


# ============================================================================
# GitHub Repo Stats Checks
# ============================================================================

@dg.asset_check(asset="fct_github_repo_stats", blocking=True)
def pandera_check_github_repo_stats(
    context,
    pandera_validator: PanderaValidatorResource
) -> dg.AssetCheckResult:
    """Validate GitHub repo stats against Pandera schema."""
    branch = context.run.tags.get("branch", "main")
    result = pandera_validator.validate_table(
        "fct_github_repo_stats",
        FactGitHubRepoStats,
        branch
    )

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "critical_failures": result.get("critical_failures", []),
            "warnings": result.get("warnings", [])
        }
    )


@dg.asset_check(asset="fct_github_repo_stats", blocking=True)
def dbt_tests_github_repo_stats(
    context,
    dbt_validator: DBTValidatorResource
) -> dg.AssetCheckResult:
    """Run dbt tests for GitHub repo stats model."""
    branch = context.run.tags.get("branch", "main")
    result = dbt_validator.run_tests_for_model("fct_github_repo_stats", branch)

    return dg.AssetCheckResult(
        passed=result["all_passed"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "tests_run": result["tests_run"],
            "passed": result["passed"],
            "failed": result["failed"],
            "failures": result.get("failures", [])
        }
    )


@dg.asset_check(asset="fct_github_repo_stats", blocking=False)
def freshness_check_github_repo_stats(
    context,
    freshness_validator: FreshnessValidatorResource
) -> dg.AssetCheckResult:
    """Check freshness of GitHub repo stats data."""
    result = freshness_validator.check_asset_freshness(context, "dlt_github_repo_stats")

    severity = (
        dg.AssetCheckSeverity.ERROR
        if config.freshness_blocks_promotion
        else dg.AssetCheckSeverity.WARN
    )

    return dg.AssetCheckResult(
        passed=result["fresh"],
        severity=severity,
        metadata={
            "age_hours": result.get("age_hours"),
            "threshold_hours": result["threshold_hours"],
            "last_updated": result.get("last_updated")
        }
    )


@dg.asset_check(asset="fct_github_repo_stats", blocking=True)
def schema_compatibility_github_repo_stats(
    context,
    schema_validator: SchemaCompatibilityValidatorResource
) -> dg.AssetCheckResult:
    """Validate schema compatibility with main branch."""
    branch = context.run.tags.get("branch", "main")

    if branch == "main":
        return dg.AssetCheckResult(
            passed=True,
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={"note": "Already on main branch"}
        )

    result = schema_validator.check_table_compatibility(
        "silver.fct_github_repo_stats",
        branch,
        "main"
    )

    return dg.AssetCheckResult(
        passed=result["compatible"],
        severity=dg.AssetCheckSeverity.ERROR,
        metadata={
            "branch": branch,
            "breaking_changes": result.get("breaking_changes", []),
            "additive_changes": result.get("additive_changes", [])
        }
    )
