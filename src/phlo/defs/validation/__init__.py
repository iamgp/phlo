"""
Validation package for Cascade data quality gates.

This package contains validation resources and asset checks that validate
data quality for all fact tables.

Components:
-----------
- PanderaValidatorResource: Validates data using Pandera schemas with severity-based blocking
- DBTValidatorResource: Runs dbt tests and parses results
- FreshnessValidatorResource: Checks data freshness against configured thresholds
- SchemaCompatibilityValidatorResource: Validates schema compatibility between branches
- asset_checks: Asset checks attached to fact tables for automatic validation
"""

import dagster as dg
from phlo.defs.validation.dbt_validator import DBTValidatorResource
from phlo.defs.validation.freshness_validator import FreshnessValidatorResource
from phlo.defs.validation.pandera_validator import PanderaValidatorResource
from phlo.defs.validation.schema_validator import SchemaCompatibilityValidatorResource

# Import all asset checks
from phlo.defs.validation.asset_checks import (
    # Glucose readings checks
    pandera_check_glucose_readings,
    dbt_tests_glucose_readings,
    freshness_check_glucose_readings,
    schema_compatibility_glucose_readings,
    # Daily glucose metrics checks
    pandera_check_daily_glucose_metrics,
    dbt_tests_daily_glucose_metrics,
    freshness_check_daily_glucose_metrics,
    schema_compatibility_daily_glucose_metrics,
    # GitHub user events checks
    pandera_check_github_user_events,
    dbt_tests_github_user_events,
    freshness_check_github_user_events,
    schema_compatibility_github_user_events,
    # GitHub repo stats checks
    pandera_check_github_repo_stats,
    dbt_tests_github_repo_stats,
    freshness_check_github_repo_stats,
    schema_compatibility_github_repo_stats,
)

__all__ = [
    "PanderaValidatorResource",
    "DBTValidatorResource",
    "FreshnessValidatorResource",
    "SchemaCompatibilityValidatorResource",
    # Asset checks
    "pandera_check_glucose_readings",
    "dbt_tests_glucose_readings",
    "freshness_check_glucose_readings",
    "schema_compatibility_glucose_readings",
    "pandera_check_daily_glucose_metrics",
    "dbt_tests_daily_glucose_metrics",
    "freshness_check_daily_glucose_metrics",
    "schema_compatibility_daily_glucose_metrics",
    "pandera_check_github_user_events",
    "dbt_tests_github_user_events",
    "freshness_check_github_user_events",
    "schema_compatibility_github_user_events",
    "pandera_check_github_repo_stats",
    "dbt_tests_github_repo_stats",
    "freshness_check_github_repo_stats",
    "schema_compatibility_github_repo_stats",
]


def build_defs() -> dg.Definitions:
    """Build validation definitions with asset checks."""
    return dg.Definitions(
        asset_checks=[
            # Glucose readings checks
            pandera_check_glucose_readings,
            dbt_tests_glucose_readings,
            freshness_check_glucose_readings,
            schema_compatibility_glucose_readings,
            # Daily glucose metrics checks
            pandera_check_daily_glucose_metrics,
            dbt_tests_daily_glucose_metrics,
            freshness_check_daily_glucose_metrics,
            schema_compatibility_daily_glucose_metrics,
            # GitHub user events checks
            pandera_check_github_user_events,
            dbt_tests_github_user_events,
            freshness_check_github_user_events,
            schema_compatibility_github_user_events,
            # GitHub repo stats checks
            pandera_check_github_repo_stats,
            dbt_tests_github_repo_stats,
            freshness_check_github_repo_stats,
            schema_compatibility_github_repo_stats,
        ],
    )
