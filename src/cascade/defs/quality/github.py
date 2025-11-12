# github.py - Quality checks for GitHub user events and repository statistics using Pandera schema validation
# Implements data quality assurance for the silver layer, ensuring processed GitHub data
# conforms to business rules, data types, and expected ranges

from __future__ import annotations

import pandas as pd
import pandera.errors
from dagster import AssetCheckResult, AssetKey, MetadataValue, asset_check

from cascade.defs.resources.trino import TrinoResource
from cascade.schemas.github import (
    FactGitHubRepoStats,
    FactGitHubUserEvents,
    GitHubRepoStats,
    GitHubUserEvents,
    VALID_EVENT_TYPES,
    get_github_repo_stats_dagster_type,
    get_github_user_events_dagster_type,
)

# --- Query Templates ---
# SQL query templates for data validation
USER_EVENTS_QUERY_BASE = """
SELECT
    id,
    type,
    actor,
    repo,
    payload,
    public,
    created_at,
    org
FROM iceberg_dev.silver.fct_github_user_events
"""

REPO_STATS_QUERY_BASE = """
SELECT
    repo_name,
    repo_full_name,
    repo_id,
    collection_date,
    contributors_data,
    commit_activity_data,
    code_frequency_data,
    participation_data
FROM iceberg_dev.silver.fct_github_repo_stats
"""


# --- Asset Checks ---
# Dagster asset checks for data quality validation
@asset_check(
    name="github_user_events_quality",
    asset=AssetKey(["fct_github_user_events"]),
    blocking=True,
    description="Validate processed GitHub user events using Pandera schema validation.",
)
def github_user_events_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check using Pandera for type-safe schema validation.

    Validates user events against the GitHubUserEvents schema,
    checking data types, ranges, and business rules directly against Iceberg via Trino.
    """
    query = USER_EVENTS_QUERY_BASE
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = (
            f"{USER_EVENTS_QUERY_BASE}\n"
            f"WHERE DATE(created_at) = DATE '{partition_date}'"
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

        events_df = pd.DataFrame(rows, columns=columns)

        # Explicitly cast columns to correct types (Trino client may return some as strings)
        type_conversions = {
            "public": "bool",
            "repo_id": "int64",  # For repo stats, but keeping for consistency
        }
        for col, dtype in type_conversions.items():
            if col in events_df.columns:
                events_df[col] = events_df[col].astype(dtype)

        # Convert timestamp if it's not already datetime
        if "created_at" in events_df.columns:
            events_df["created_at"] = pd.to_datetime(events_df["created_at"])

        context.log.info(
            "Loaded %d rows from iceberg_dev.silver.fct_github_user_events", len(events_df)
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

    if events_df.empty:
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
        GitHubUserEvents.validate(events_df, lazy=True)

        context.log.info("All validation checks passed!")

        # Build schema metadata for UI display
        schema_info = {
            "id": "str (unique, non-null)",
            "type": f"str ({', '.join(VALID_EVENT_TYPES)}, non-null)",
            "actor": "str (JSON, non-null)",
            "repo": "str (JSON, non-null)",
            "payload": "str (JSON, non-null)",
            "public": "bool (non-null)",
            "created_at": "datetime (non-null)",
            "org": "str (JSON, nullable)",
        }

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(events_df)),
                "columns_validated": MetadataValue.int(len(events_df.columns)),
                "schema_version": MetadataValue.text("1.0.0"),
                "pandera_schema": MetadataValue.md(
                    "## Validated Schema\n\n"
                    + "\n".join(
                        [f"- **{col}**: {dtype}" for col, dtype in schema_info.items()]
                    )
                ),
                "dagster_type": MetadataValue.text(str(get_github_user_events_dagster_type())),
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
                "rows_evaluated": MetadataValue.int(len(events_df)),
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


@asset_check(
    name="github_repo_stats_quality",
    asset=AssetKey(["fct_github_repo_stats"]),
    blocking=True,
    description="Validate processed GitHub repository statistics using Pandera schema validation.",
)
def github_repo_stats_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check using Pandera for type-safe schema validation.

    Validates repository statistics against the GitHubRepoStats schema,
    checking data types, ranges, and business rules directly against Iceberg via Trino.
    """
    query = REPO_STATS_QUERY_BASE
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = (
            f"{REPO_STATS_QUERY_BASE}\n"
            f"WHERE collection_date = '{partition_date}'"
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

        stats_df = pd.DataFrame(rows, columns=columns)

        # Explicitly cast columns to correct types (Trino client may return some as strings)
        type_conversions = {
            "repo_id": "int64",
        }
        for col, dtype in type_conversions.items():
            if col in stats_df.columns:
                stats_df[col] = stats_df[col].astype(dtype)

        context.log.info(
            "Loaded %d rows from iceberg_dev.silver.fct_github_repo_stats", len(stats_df)
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

    if stats_df.empty:
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
        GitHubRepoStats.validate(stats_df, lazy=True)

        context.log.info("All validation checks passed!")

        # Build schema metadata for UI display
        schema_info = {
            "repo_name": "str (non-null)",
            "repo_full_name": "str (non-null)",
            "repo_id": "int (non-null)",
            "collection_date": "str (YYYY-MM-DD, non-null)",
            "contributors_data": "str (JSON, nullable)",
            "commit_activity_data": "str (JSON, nullable)",
            "code_frequency_data": "str (JSON, nullable)",
            "participation_data": "str (JSON, nullable)",
        }

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(stats_df)),
                "columns_validated": MetadataValue.int(len(stats_df.columns)),
                "schema_version": MetadataValue.text("1.0.0"),
                "pandera_schema": MetadataValue.md(
                    "## Validated Schema\n\n"
                    + "\n".join(
                        [f"- **{col}**: {dtype}" for col, dtype in schema_info.items()]
                    )
                ),
                "dagster_type": MetadataValue.text(str(get_github_repo_stats_dagster_type())),
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
                "rows_evaluated": MetadataValue.int(len(stats_df)),
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


# --- Fact Table Asset Checks (Enriched Data) ---
# Asset checks for validating enriched fact tables with calculated fields

FACT_USER_EVENTS_QUERY = """
SELECT
    event_id,
    event_type,
    event_category,
    actor_login,
    actor_id,
    repo_name,
    repo_full_name,
    public,
    is_repo_public,
    involves_organization,
    created_at,
    event_date,
    hour_of_day,
    day_of_week,
    day_name
FROM iceberg_dev.silver.fct_github_user_events
"""

FACT_REPO_STATS_QUERY = """
SELECT
    repo_name,
    repo_full_name,
    repo_id,
    repo_owner,
    repo_short_name,
    collection_date,
    contributor_count,
    total_commits_last_52_weeks,
    weeks_with_activity,
    activity_score,
    contribution_level,
    activity_level,
    repository_health,
    avg_commits_per_week
FROM iceberg_dev.silver.fct_github_repo_stats
"""


@asset_check(
    name="fact_github_user_events_quality",
    asset=AssetKey(["fct_github_user_events"]),
    blocking=True,
    description="Validate enriched GitHub user events fact table using Pandera schema validation.",
)
def fact_github_user_events_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check for enriched GitHub user events fact table.

    Validates enriched user events with calculated fields against the FactGitHubUserEvents schema,
    checking data types, categorization, extracted JSON fields, and time dimensions.
    """
    query = FACT_USER_EVENTS_QUERY
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = f"{FACT_USER_EVENTS_QUERY}\nWHERE DATE(created_at) = DATE '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            if not cursor.description:
                return AssetCheckResult(
                    passed=False,
                    metadata={
                        "reason": MetadataValue.text("missing_column_metadata"),
                        "query": MetadataValue.text(query),
                    },
                )
            columns = [desc[0] for desc in cursor.description]

        events_df = pd.DataFrame(rows, columns=columns)

        # Type conversions
        if "hour_of_day" in events_df.columns:
            events_df["hour_of_day"] = events_df["hour_of_day"].astype("int64")
        if "day_of_week" in events_df.columns:
            events_df["day_of_week"] = events_df["day_of_week"].astype("int64")
        if "public" in events_df.columns:
            events_df["public"] = events_df["public"].astype("bool")
        if "is_repo_public" in events_df.columns:
            events_df["is_repo_public"] = events_df["is_repo_public"].astype("bool")
        if "involves_organization" in events_df.columns:
            events_df["involves_organization"] = events_df["involves_organization"].astype("bool")
        if "created_at" in events_df.columns:
            events_df["created_at"] = pd.to_datetime(events_df["created_at"])
        if "event_date" in events_df.columns:
            events_df["event_date"] = pd.to_datetime(events_df["event_date"])

        context.log.info(f"Loaded {len(events_df)} rows from fact table")
    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
                "query": MetadataValue.text(query),
            },
        )

    if events_df.empty:
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available for selected partition"),
            },
        )

    # Validate using Pandera schema
    context.log.info("Validating enriched fact data with Pandera schema...")
    try:
        FactGitHubUserEvents.validate(events_df, lazy=True)
        context.log.info("All validation checks passed!")

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(events_df)),
                "columns_validated": MetadataValue.int(len(events_df.columns)),
                "schema_version": MetadataValue.text("1.0.0"),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Schema validation failed with {len(failure_cases)} check failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(events_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(
                    failure_cases.groupby("column").size().to_dict()
                ),
                "sample_failures": MetadataValue.json(
                    failure_cases.head(20)[
                        ["schema_context", "column", "check", "failure_case"]
                    ].to_dict(orient="records")
                ),
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


@asset_check(
    name="fact_github_repo_stats_quality",
    asset=AssetKey(["fct_github_repo_stats"]),
    blocking=True,
    description="Validate enriched GitHub repo stats fact table using Pandera schema validation.",
)
def fact_github_repo_stats_quality_check(context, trino: TrinoResource) -> AssetCheckResult:
    """
    Quality check for enriched GitHub repo stats fact table.

    Validates enriched repo stats with calculated metrics against the FactGitHubRepoStats schema,
    checking contributor counts, activity scores, and classification fields.
    """
    query = FACT_REPO_STATS_QUERY
    partition_key = getattr(context, "partition_key", None)
    if partition_key is None:
        partition_key = getattr(context, "asset_partition_key", None)

    if partition_key:
        partition_date = partition_key
        query = f"{FACT_REPO_STATS_QUERY}\nWHERE collection_date = '{partition_date}'"
        context.log.info(f"Validating partition: {partition_date}")

    try:
        with trino.cursor(schema="silver") as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            if not cursor.description:
                return AssetCheckResult(
                    passed=False,
                    metadata={
                        "reason": MetadataValue.text("missing_column_metadata"),
                        "query": MetadataValue.text(query),
                    },
                )
            columns = [desc[0] for desc in cursor.description]

        stats_df = pd.DataFrame(rows, columns=columns)

        # Type conversions
        for col in ["repo_id", "contributor_count", "total_commits_last_52_weeks", "weeks_with_activity"]:
            if col in stats_df.columns:
                stats_df[col] = stats_df[col].astype("int64")

        context.log.info(f"Loaded {len(stats_df)} rows from fact table")
    except Exception as exc:
        context.log.error(f"Failed to load data from Trino: {exc}")
        return AssetCheckResult(
            passed=False,
            metadata={
                "reason": MetadataValue.text("trino_query_failed"),
                "error": MetadataValue.text(str(exc)),
                "query": MetadataValue.text(query),
            },
        )

    if stats_df.empty:
        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(0),
                "note": MetadataValue.text("No data available for selected partition"),
            },
        )

    # Validate using Pandera schema
    context.log.info("Validating enriched fact data with Pandera schema...")
    try:
        FactGitHubRepoStats.validate(stats_df, lazy=True)
        context.log.info("All validation checks passed!")

        return AssetCheckResult(
            passed=True,
            metadata={
                "rows_validated": MetadataValue.int(len(stats_df)),
                "columns_validated": MetadataValue.int(len(stats_df.columns)),
                "schema_version": MetadataValue.text("1.0.0"),
            },
        )

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.warning(f"Schema validation failed with {len(failure_cases)} check failures")

        return AssetCheckResult(
            passed=False,
            metadata={
                "rows_evaluated": MetadataValue.int(len(stats_df)),
                "failed_checks": MetadataValue.int(len(failure_cases)),
                "failures_by_column": MetadataValue.json(
                    failure_cases.groupby("column").size().to_dict()
                ),
                "sample_failures": MetadataValue.json(
                    failure_cases.head(20)[
                        ["schema_context", "column", "check", "failure_case"]
                    ].to_dict(orient="records")
                ),
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
