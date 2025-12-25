"""Quality checks for GitHub data using @phlo_quality decorator.

Demonstrates phlo's declarative quality check framework with multiple check types
including reconciliation checks for cross-table data validation.
"""

from phlo_quality import (
    AggregateConsistencyCheck,
    CountCheck,
    NullCheck,
    PatternCheck,
    RangeCheck,
    ReconciliationCheck,
    SchemaCheck,
    UniqueCheck,
    phlo_quality,
)

from workflows.schemas.github import RawUserEvents


@phlo_quality(
    table="raw.user_events",
    checks=[
        NullCheck(columns=["id", "type", "created_at"]),
        UniqueCheck(columns=["id"]),
        SchemaCheck(schema=RawUserEvents),
        CountCheck(min_rows=1),
    ],
    group="github",
    blocking=True,
)
def user_events_quality():
    """Quality checks for GitHub user events."""
    pass


@phlo_quality(
    table="raw.user_repos",
    checks=[
        NullCheck(columns=["id", "name", "created_at"]),
        UniqueCheck(columns=["id"]),
        RangeCheck(column="stargazers_count", min_value=0, max_value=1000000),
        RangeCheck(column="forks_count", min_value=0, max_value=100000),
        CountCheck(min_rows=1),
    ],
    group="github",
    blocking=True,
)
def user_repos_quality():
    """Quality checks for GitHub repositories."""
    pass


@phlo_quality(
    table="raw.user_profile",
    checks=[
        NullCheck(columns=["id", "login"]),
        UniqueCheck(columns=["id"]),
        PatternCheck(
            column="login", pattern=r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
        ),
        RangeCheck(column="followers", min_value=0, max_value=1000000),
        RangeCheck(column="following", min_value=0, max_value=10000),
    ],
    group="github",
    blocking=True,
)
def user_profile_quality():
    """Quality checks for GitHub user profile."""
    pass


# =============================================================================
# RECONCILIATION CHECKS
# Cross-table data validation to ensure consistency across pipeline layers
# =============================================================================


@phlo_quality(
    table="gold.fct_github_events",
    checks=[
        # Verify row count matches staging layer (1:1 transform)
        ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.0,  # Exact match required
        ),
    ],
    group="github_reconciliation",
    blocking=True,
    partition_aware=True,
)
def events_reconciliation():
    """Reconciliation: fct_github_events row count matches stg_github_events.

    This check ensures no rows are lost or duplicated during the silver->gold
    transformation. Since fct_github_events is a 1:1 grain with stg_github_events,
    row counts should match exactly per partition.

    Debugging a failure:
    1. Check the 'query' in check metadata to see the source count SQL
    2. Compare _phlo_partition_date values between tables
    3. Look for filter conditions that might exclude rows
    """
    pass


@phlo_quality(
    table="gold.fct_daily_github_metrics",
    checks=[
        # Verify total_events aggregate matches source row count
        AggregateConsistencyCheck(
            source_table="gold.fct_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            partition_column="_phlo_partition_date",
            group_by=["activity_date"],
            tolerance=0.0,  # Exact match
        ),
    ],
    group="github_reconciliation",
    blocking=True,
    partition_aware=True,
)
def daily_metrics_aggregate_consistency():
    """Reconciliation: fct_daily_github_metrics.total_events matches source count.

    This check verifies that the aggregated total_events in the daily metrics
    table matches COUNT(*) from the source events table for each activity_date.

    Debugging a failure:
    1. Use the 'query' in check metadata to see the source aggregation SQL
    2. Check for GROUP BY mismatches (activity_date vs event_date)
    3. Verify DISTINCT handling if using COUNT(DISTINCT ...)
    """
    pass
