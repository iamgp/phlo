"""
Reconciliation quality checks for cross-table data validation.

These checks compare data between tables to ensure consistency across pipeline layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

import pandas as pd

from phlo.quality.checks import QualityCheck, QualityCheckResult


@dataclass
class ReconciliationCheck(QualityCheck):
    """
    Check row count parity between source and target tables.

    This check compares row counts between two tables to ensure
    data is not lost or duplicated during transformation.

    Example:
        ```python
        ReconciliationCheck(
            source_table="silver.stg_github_events",
            partition_column="_phlo_partition_date",
            check_type="rowcount_parity",
            tolerance=0.0,  # Exact match required
        )
        ```
    """

    source_table: str
    """Fully qualified source table name (e.g., 'silver.stg_github_events')."""

    partition_column: str = "_phlo_partition_date"
    """Column used for partition filtering."""

    check_type: str = "rowcount_parity"
    """Type of reconciliation: 'rowcount_parity' or 'rowcount_gte'."""

    tolerance: float = 0.0
    """Allowed percentage difference (0.0 = exact match, 0.05 = 5% tolerance)."""

    where_clause: Optional[str] = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute reconciliation check comparing row counts."""
        target_count = len(df)

        # Get partition key from context if available
        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        # Build the source count query
        source_query = self._build_source_query(partition_key)

        # Try to get source count from Trino
        source_count = self._get_source_count(context, source_query)

        if source_count is None:
            return QualityCheckResult(
                passed=False,
                metric_name="reconciliation_check",
                metric_value={"target_count": target_count, "source_count": None},
                metadata={
                    "source_table": self.source_table,
                    "query": source_query,
                    "note": "Could not query source table",
                },
                failure_message=f"Failed to query source table {self.source_table}",
            )

        # Calculate difference
        if source_count == 0 and target_count == 0:
            diff_pct = 0.0
        elif source_count == 0:
            diff_pct = 1.0  # 100% difference if source is empty but target is not
        else:
            diff_pct = abs(target_count - source_count) / source_count

        # Determine pass/fail based on check type
        if self.check_type == "rowcount_parity":
            passed = diff_pct <= self.tolerance
        elif self.check_type == "rowcount_gte":
            # Target should have at least as many rows as source
            passed = target_count >= source_count * (1 - self.tolerance)
        else:
            passed = diff_pct <= self.tolerance

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Row count reconciliation failed: target has {target_count} rows, "
                f"source has {source_count} rows (diff: {diff_pct:.2%}, "
                f"tolerance: {self.tolerance:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="reconciliation_check",
            metric_value={
                "target_count": target_count,
                "source_count": source_count,
                "difference_pct": float(diff_pct),
            },
            metadata={
                "source_table": self.source_table,
                "check_type": self.check_type,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "query": source_query,
            },
            failure_message=failure_msg,
        )

    def _build_source_query(self, partition_key: Optional[str]) -> str:
        """Build SQL query to count source rows."""
        query = f"SELECT COUNT(*) FROM {self.source_table}"

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        if self.where_clause:
            conditions.append(f"({self.where_clause})")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query

    def _get_source_count(self, context: Any, query: str) -> Optional[int]:
        """Execute query to get source row count."""
        try:
            # Try to use Trino resource from context
            if hasattr(context, "resources") and hasattr(context.resources, "trino"):
                trino = context.resources.trino
                result = trino.execute_query(query)
                if result and len(result) > 0:
                    return int(result[0][0])

        except Exception as e:
            if hasattr(context, "log"):
                context.log.warning(f"Failed to query source: {e}")
            return None

    @property
    def name(self) -> str:
        return f"reconciliation_{self.source_table.replace('.', '_')}"


@dataclass
class AggregateConsistencyCheck(QualityCheck):
    """
    Check that computed aggregates match source data.

    This check verifies that aggregated values in a target table
    match the expected computation from source data.

    Example:
        ```python
        AggregateConsistencyCheck(
            source_table="silver.stg_github_events",
            aggregate_column="total_events",
            source_expression="COUNT(*)",
            partition_column="_phlo_partition_date",
            group_by=["activity_date"],
            tolerance=0.0,
        )
        ```
    """

    source_table: str
    """Fully qualified source table name."""

    aggregate_column: str
    """Column in target table containing the aggregate value."""

    source_expression: str
    """SQL expression to compute from source (e.g., 'COUNT(*)', 'SUM(amount)')."""

    partition_column: str = "_phlo_partition_date"
    """Column used for partition filtering."""

    group_by: List[str] = field(default_factory=list)
    """Columns to group by when comparing aggregates."""

    tolerance: float = 0.0
    """Allowed percentage difference (0.0 = exact match)."""

    where_clause: Optional[str] = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: Any) -> QualityCheckResult:
        """Execute aggregate consistency check."""
        if self.aggregate_column not in df.columns:
            return QualityCheckResult(
                passed=False,
                metric_name="aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Column '{self.aggregate_column}' not found in target data",
            )

        # Get partition key from context if available
        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key

        # Build source query
        source_query = self._build_source_query(partition_key)

        # Get expected values from source
        source_values = self._get_source_aggregates(context, source_query)

        if source_values is None:
            return QualityCheckResult(
                passed=False,
                metric_name="aggregate_consistency_check",
                metric_value=None,
                metadata={
                    "source_table": self.source_table,
                    "query": source_query,
                },
                failure_message=f"Failed to query source aggregates from {self.source_table}",
            )

        # Compare target vs source
        mismatches = []
        total_checks = 0

        if self.group_by:
            # Group-level comparison
            for _, row in df.iterrows():
                group_key = tuple(row[col] for col in self.group_by if col in df.columns)
                target_value = row[self.aggregate_column]

                # Find matching source value
                source_value = source_values.get(group_key)
                if source_value is not None:
                    total_checks += 1
                    if not self._values_match(target_value, source_value):
                        mismatches.append(
                            {
                                "group_key": str(group_key),
                                "target": target_value,
                                "source": source_value,
                            }
                        )
        else:
            # Single value comparison (sum of all)
            target_total = df[self.aggregate_column].sum()
            source_total = sum(source_values.values()) if source_values else 0
            total_checks = 1

            if not self._values_match(target_total, source_total):
                mismatches.append(
                    {
                        "target_total": target_total,
                        "source_total": source_total,
                    }
                )

        passed = len(mismatches) == 0

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Aggregate consistency check failed: {len(mismatches)} mismatches "
                f"out of {total_checks} checked (tolerance: {self.tolerance:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="aggregate_consistency_check",
            metric_value={
                "mismatches": len(mismatches),
                "total_checked": total_checks,
            },
            metadata={
                "source_table": self.source_table,
                "aggregate_column": self.aggregate_column,
                "source_expression": self.source_expression,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "query": source_query,
                "sample_mismatches": mismatches[:10],  # Limit to 10 samples
            },
            failure_message=failure_msg,
        )

    def _values_match(self, target: Any, source: Any) -> bool:
        """Check if target and source values match within tolerance."""
        try:
            target_val = float(target) if target is not None else 0.0
            source_val = float(source) if source is not None else 0.0

            if source_val == 0 and target_val == 0:
                return True
            if source_val == 0:
                return False

            diff_pct = abs(target_val - source_val) / abs(source_val)
            return diff_pct <= self.tolerance
        except (TypeError, ValueError):
            return target == source

    def _build_source_query(self, partition_key: Optional[str]) -> str:
        """Build SQL query to compute source aggregates."""
        select_cols = ", ".join(self.group_by) if self.group_by else "1 as grp"
        query = (
            f"SELECT {select_cols}, {self.source_expression} as agg_value FROM {self.source_table}"
        )

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        if self.where_clause:
            conditions.append(f"({self.where_clause})")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if self.group_by:
            query += " GROUP BY " + ", ".join(self.group_by)

        return query

    def _get_source_aggregates(self, context: Any, query: str) -> Optional[dict[tuple, Any]]:
        """Execute query to get source aggregate values."""
        try:
            # Try to use Trino resource from context
            if hasattr(context, "resources") and hasattr(context.resources, "trino"):
                trino = context.resources.trino
                result = trino.execute_query(query)
                if result:
                    # Build dict of group_key -> aggregate_value
                    values = {}
                    for row in result:
                        if self.group_by:
                            key = tuple(row[:-1])  # All but last column
                            values[key] = row[-1]  # Last column is aggregate
                        else:
                            values[()] = row[-1]
                    return values

            # For testing without Trino, return None
            return None

        except Exception as e:
            if hasattr(context, "log"):
                context.log.warning(f"Failed to query source aggregates: {e}")
            return None

    @property
    def name(self) -> str:
        return f"aggregate_consistency_{self.aggregate_column}"
