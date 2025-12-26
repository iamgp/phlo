"""Tests for reconciliation quality checks.

Tests the ReconciliationCheck and AggregateConsistencyCheck classes.
"""

from unittest.mock import MagicMock

import pandas as pd

from phlo_quality.reconciliation import AggregateConsistencyCheck, ReconciliationCheck


class TestReconciliationCheck:
    """Tests for ReconciliationCheck class."""

    def test_check_passes_when_counts_match(self):
        """Test that check passes when target and source counts match."""
        # Create target dataframe with 100 rows
        df = pd.DataFrame({"id": range(100), "value": range(100)})

        # Mock context with Trino that returns matching count
        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [(100,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is True
        assert result.metric_value["target_count"] == 100
        assert result.metric_value["source_count"] == 100
        assert result.metric_value["difference_pct"] == 0.0

    def test_check_fails_when_counts_differ(self):
        """Test that check fails when target and source counts differ."""
        df = pd.DataFrame({"id": range(100), "value": range(100)})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        # Source has 120 rows but target has 100
        context.resources.trino.execute_query.return_value = [(120,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is False
        assert result.metric_value["target_count"] == 100
        assert result.metric_value["source_count"] == 120
        assert result.failure_message is not None
        assert "reconciliation failed" in result.failure_message.lower()

    def test_check_passes_within_tolerance(self):
        """Test that check passes when difference is within tolerance."""
        df = pd.DataFrame({"id": range(95), "value": range(95)})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [(100,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.05,  # 5% tolerance
        )

        result = check.execute(df, context)

        assert result.passed is True
        assert result.metric_value["difference_pct"] == 0.05

    def test_check_fails_outside_tolerance(self):
        """Test that check fails when difference exceeds tolerance."""
        df = pd.DataFrame({"id": range(90), "value": range(90)})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [(100,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.05,  # 5% tolerance, but difference is 10%
        )

        result = check.execute(df, context)

        assert result.passed is False
        assert result.metric_value["difference_pct"] == 0.10

    def test_rowcount_gte_passes_when_target_has_more(self):
        """Test rowcount_gte check passes when target >= source."""
        df = pd.DataFrame({"id": range(110), "value": range(110)})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [(100,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_gte",
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is True

    def test_handles_empty_dataframes(self):
        """Test that check handles empty target and source correctly."""
        df = pd.DataFrame({"id": [], "value": []})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [(0,)]

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
        )

        result = check.execute(df, context)

        assert result.passed is True
        assert result.metric_value["target_count"] == 0
        assert result.metric_value["source_count"] == 0

    def test_handles_missing_trino_connection(self):
        """Test that check handles missing Trino connection gracefully."""
        df = pd.DataFrame({"id": range(100), "value": range(100)})

        context = MagicMock()
        context.partition_key = "2024-01-01"
        # Simulate Trino connection failure
        del context.resources.trino

        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
        )

        result = check.execute(df, context)

        assert result.passed is False
        assert "failed to query source table" in result.failure_message.lower()

    def test_name_property(self):
        """Test that check name is correctly generated."""
        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
        )

        assert check.name == "reconciliation_silver_stg_github_events"

    def test_builds_query_with_partition_filter(self):
        """Test that source query includes partition filter."""
        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
        )

        query = check._build_source_query("2024-01-01")

        assert "SELECT COUNT(*) FROM silver.stg_github_events" in query
        assert "_phlo_partition_date = '2024-01-01'" in query

    def test_builds_query_with_where_clause(self):
        """Test that source query includes custom WHERE clause."""
        check = ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            where_clause="event_type = 'PushEvent'",
        )

        query = check._build_source_query("2024-01-01")

        assert "event_type = 'PushEvent'" in query


class TestAggregateConsistencyCheck:
    """Tests for AggregateConsistencyCheck class."""

    def test_check_passes_when_aggregates_match(self):
        """Test that check passes when aggregates match."""
        # Target has pre-computed aggregates
        df = pd.DataFrame(
            {
                "activity_date": ["2024-01-01", "2024-01-02"],
                "total_events": [50, 75],
            }
        )

        context = MagicMock()
        context.partition_key = "2024-01-01"
        # Source returns matching aggregates
        context.resources.trino.execute_query.return_value = [
            ("2024-01-01", 50),
            ("2024-01-02", 75),
        ]

        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            partition_column="_phlo_partition_date",
            group_by=["activity_date"],
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is True
        assert result.metric_value["mismatches"] == 0

    def test_check_fails_when_aggregates_differ(self):
        """Test that check fails when aggregates don't match."""
        df = pd.DataFrame(
            {
                "activity_date": ["2024-01-01"],
                "total_events": [50],
            }
        )

        context = MagicMock()
        context.partition_key = "2024-01-01"
        # Source returns different aggregate
        context.resources.trino.execute_query.return_value = [
            ("2024-01-01", 60),  # Different from target's 50
        ]

        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            group_by=["activity_date"],
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is False
        assert result.metric_value["mismatches"] == 1
        assert "mismatch" in result.failure_message.lower()

    def test_check_passes_within_tolerance(self):
        """Test that check passes when difference is within tolerance."""
        df = pd.DataFrame(
            {
                "activity_date": ["2024-01-01"],
                "total_events": [95],  # 5% less than source
            }
        )

        context = MagicMock()
        context.partition_key = "2024-01-01"
        context.resources.trino.execute_query.return_value = [
            ("2024-01-01", 100),
        ]

        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            group_by=["activity_date"],
            tolerance=0.05,  # 5% tolerance
        )

        result = check.execute(df, context)

        assert result.passed is True

    def test_handles_missing_column(self):
        """Test that check handles missing aggregate column."""
        df = pd.DataFrame(
            {
                "activity_date": ["2024-01-01"],
                # Missing 'total_events' column
            }
        )

        context = MagicMock()

        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
        )

        result = check.execute(df, context)

        assert result.passed is False
        assert "not found" in result.failure_message.lower()

    def test_single_aggregate_comparison(self):
        """Test aggregate check without grouping (total sum comparison)."""
        df = pd.DataFrame(
            {
                "total_events": [10, 20, 30],  # Sum = 60
            }
        )

        context = MagicMock()
        context.partition_key = "2024-01-01"
        # Source returns total of 60
        context.resources.trino.execute_query.return_value = [(60,)]

        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="SUM(events)",
            group_by=[],  # No grouping
            tolerance=0.0,
        )

        result = check.execute(df, context)

        assert result.passed is True

    def test_name_property(self):
        """Test that check name is correctly generated."""
        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
        )

        assert check.name == "aggregate_consistency_total_events"

    def test_builds_query_with_group_by(self):
        """Test that source query includes GROUP BY clause."""
        check = AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            group_by=["activity_date", "event_type"],
        )

        query = check._build_source_query("2024-01-01")

        assert "COUNT(*)" in query
        assert "GROUP BY activity_date, event_type" in query
