"""
Reconciliation quality checks for cross-table data validation.

These checks compare data between tables to ensure consistency across pipeline layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd

from phlo_quality.checks import QualityCheck, QualityCheckResult

if TYPE_CHECKING:
    from dagster import AssetExecutionContext


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

    absolute_tolerance: int | float | None = None
    """Allowed absolute difference in row counts (None = disable)."""

    where_clause: str | None = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: "AssetExecutionContext") -> QualityCheckResult:
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
        diff_abs = abs(target_count - source_count)

        # Determine pass/fail based on check type
        if self.check_type == "rowcount_parity":
            passed = diff_pct <= self.tolerance or (
                self.absolute_tolerance is not None and diff_abs <= self.absolute_tolerance
            )
        elif self.check_type == "rowcount_gte":
            # Target should have at least as many rows as source
            passed = target_count >= source_count * (1 - self.tolerance) or (
                self.absolute_tolerance is not None
                and target_count >= source_count - self.absolute_tolerance
            )
        else:
            passed = diff_pct <= self.tolerance or (
                self.absolute_tolerance is not None and diff_abs <= self.absolute_tolerance
            )

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Row count reconciliation failed: target has {target_count} rows, "
                f"source has {source_count} rows (diff: {diff_pct:.2%}, "
                f"tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="reconciliation_check",
            metric_value={
                "target_count": target_count,
                "source_count": source_count,
                "difference_pct": float(diff_pct),
                "difference_abs": int(diff_abs),
            },
            metadata={
                "source_table": self.source_table,
                "check_type": self.check_type,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "query": source_query,
            },
            failure_message=failure_msg,
        )

    def _build_source_query(self, partition_key: str | None) -> str:
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

    def _get_source_count(self, context: "AssetExecutionContext", query: str) -> int | None:
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

    group_by: list[str] = field(default_factory=list)
    """Columns to group by when comparing aggregates."""

    tolerance: float = 0.0
    """Allowed percentage difference (0.0 = exact match)."""

    absolute_tolerance: int | float | None = None
    """Allowed absolute difference in aggregate values (None = disable)."""

    where_clause: str | None = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: "AssetExecutionContext") -> QualityCheckResult:
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
                f"out of {total_checks} checked (tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
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
                "absolute_tolerance": self.absolute_tolerance,
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
                if self.absolute_tolerance is not None:
                    return abs(target_val) <= self.absolute_tolerance
                return False

            diff_pct = abs(target_val - source_val) / abs(source_val)
            if diff_pct <= self.tolerance:
                return True
            if self.absolute_tolerance is not None:
                return abs(target_val - source_val) <= self.absolute_tolerance
            return False
        except (TypeError, ValueError):
            return target == source

    def _build_source_query(self, partition_key: str | None) -> str:
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

    def _get_source_aggregates(
        self, context: "AssetExecutionContext", query: str
    ) -> dict[tuple, Any] | None:
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


@dataclass(frozen=True)
class AggregateSpec:
    """Aggregate definition for multi-aggregate reconciliation."""

    name: str
    """Alias used for the source aggregate expression."""

    expression: str
    """SQL expression to compute from source (e.g., 'COUNT(*)', 'SUM(amount)')."""

    target_column: str
    """Column in target table containing the aggregate value."""


@dataclass
class KeyParityCheck(QualityCheck):
    """
    Check that source and target tables have matching keys.

    This check compares distinct keys between source and target tables to catch
    missing or extra rows even when row counts match.
    """

    source_table: str
    """Fully qualified source table name."""

    key_columns: list[str]
    """Primary key or composite key columns used for alignment."""

    partition_column: str = "_phlo_partition_date"
    """Column used for partition filtering."""

    tolerance: float = 0.0
    """Allowed fraction of missing keys (0.0 = exact match)."""

    where_clause: str | None = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: "AssetExecutionContext") -> QualityCheckResult:
        """Execute key parity check."""
        missing_columns = [column for column in self.key_columns if column not in df.columns]
        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="key_parity_check",
                metric_value=None,
                failure_message=f"Missing key columns in target data: {missing_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_source_query(partition_key)
        source_rows = self._get_source_rows(context, source_query)

        if source_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="key_parity_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source keys from {self.source_table}",
            )

        source_keys = {tuple(row) for row in source_rows}
        target_keys = {
            tuple(row)
            for row in df[self.key_columns].drop_duplicates().itertuples(index=False, name=None)
        }

        missing_in_target = source_keys - target_keys
        missing_in_source = target_keys - source_keys

        total_keys = len(source_keys.union(target_keys))
        mismatch_count = len(missing_in_target) + len(missing_in_source)
        mismatch_pct = mismatch_count / total_keys if total_keys else 0.0

        passed = mismatch_pct <= self.tolerance

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Key parity check failed: {len(missing_in_target)} missing in target, "
                f"{len(missing_in_source)} missing in source "
                f"(mismatch: {mismatch_pct:.2%}, tolerance: {self.tolerance:.2%})"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="key_parity_check",
            metric_value={
                "missing_in_target": len(missing_in_target),
                "missing_in_source": len(missing_in_source),
                "total_keys": total_keys,
                "mismatch_pct": float(mismatch_pct),
            },
            metadata={
                "source_table": self.source_table,
                "key_columns": self.key_columns,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "query": source_query,
                "sample_missing_in_target": [str(key) for key in list(missing_in_target)[:10]],
                "sample_missing_in_source": [str(key) for key in list(missing_in_source)[:10]],
            },
            failure_message=failure_msg,
        )

    def _build_source_query(self, partition_key: str | None) -> str:
        """Build SQL query to fetch distinct source keys."""
        select_cols = ", ".join(self.key_columns)
        query = f"SELECT DISTINCT {select_cols} FROM {self.source_table}"

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        if self.where_clause:
            conditions.append(f"({self.where_clause})")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query

    def _get_source_rows(self, context: "AssetExecutionContext", query: str) -> list[tuple] | None:
        """Execute query to fetch source keys."""
        try:
            if hasattr(context, "resources") and hasattr(context.resources, "trino"):
                trino = context.resources.trino
                result = trino.execute_query(query)
                if result is not None:
                    return [tuple(row) for row in result]
        except Exception as exc:
            if hasattr(context, "log"):
                context.log.warning(f"Failed to query source keys: {exc}")
            return None
        return None

    @property
    def name(self) -> str:
        return f"key_parity_{self.source_table.replace('.', '_')}"


@dataclass
class MultiAggregateConsistencyCheck(QualityCheck):
    """
    Check that multiple aggregates match source data.

    This check compares multiple aggregates in a single query to reduce
    repeated scans of the source table.
    """

    source_table: str
    """Fully qualified source table name."""

    aggregates: list[AggregateSpec]
    """Aggregates to compare against target data."""

    partition_column: str = "_phlo_partition_date"
    """Column used for partition filtering."""

    group_by: list[str] = field(default_factory=list)
    """Columns to group by when comparing aggregates."""

    tolerance: float = 0.0
    """Allowed percentage difference (0.0 = exact match)."""

    absolute_tolerance: int | float | None = None
    """Allowed absolute difference in aggregate values (None = disable)."""

    where_clause: str | None = None
    """Optional WHERE clause to filter source data."""

    def execute(self, df: pd.DataFrame, context: "AssetExecutionContext") -> QualityCheckResult:
        """Execute multi-aggregate consistency check."""
        if not self.aggregates:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message="No aggregates provided for comparison",
            )

        aggregate_names = [agg.name for agg in self.aggregates]
        if len(set(aggregate_names)) != len(aggregate_names):
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message="Aggregate names must be unique",
            )

        missing_target_columns = [
            agg.target_column for agg in self.aggregates if agg.target_column not in df.columns
        ]
        if missing_target_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Missing target columns: {missing_target_columns}",
            )

        missing_group_columns = [column for column in self.group_by if column not in df.columns]
        if missing_group_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                failure_message=f"Missing group_by columns: {missing_group_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_source_query(partition_key)
        source_values = self._get_source_aggregates(context, source_query)

        if source_values is None:
            return QualityCheckResult(
                passed=False,
                metric_name="multi_aggregate_consistency_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source aggregates from {self.source_table}",
            )

        mismatches: list[dict[str, Any]] = []

        if self.group_by:
            target_keys = {
                tuple(row)
                for row in df[self.group_by].drop_duplicates().itertuples(index=False, name=None)
            }
            source_keys = set(source_values.keys())

            missing_in_target = source_keys - target_keys
            missing_in_source = target_keys - source_keys

            for key in missing_in_source:
                for aggregate in self.aggregates:
                    mismatches.append(
                        {
                            "group_key": str(key),
                            "aggregate": aggregate.name,
                            "reason": "missing_in_source",
                        }
                    )

            for key in missing_in_target:
                for aggregate in self.aggregates:
                    mismatches.append(
                        {
                            "group_key": str(key),
                            "aggregate": aggregate.name,
                            "reason": "missing_in_target",
                        }
                    )

            for _, row in df.iterrows():
                group_key = tuple(row[col] for col in self.group_by)
                if group_key not in source_values:
                    continue
                source_row = source_values[group_key]
                for aggregate in self.aggregates:
                    target_value = row[aggregate.target_column]
                    source_value = source_row.get(aggregate.name)
                    if not self._values_match(target_value, source_value):
                        mismatches.append(
                            {
                                "group_key": str(group_key),
                                "aggregate": aggregate.name,
                                "target": target_value,
                                "source": source_value,
                            }
                        )
        else:
            target_totals = {agg.name: df[agg.target_column].sum() for agg in self.aggregates}
            source_total = source_values.get(()) if source_values else None
            for aggregate in self.aggregates:
                target_value = target_totals.get(aggregate.name)
                source_value = source_total.get(aggregate.name) if source_total else None
                if not self._values_match(target_value, source_value):
                    mismatches.append(
                        {
                            "aggregate": aggregate.name,
                            "target": target_value,
                            "source": source_value,
                        }
                    )

        passed = len(mismatches) == 0
        total_checks = max(len(self.aggregates), 1)
        if self.group_by:
            total_checks = max(len(source_values), len(df)) * len(self.aggregates)

        failure_msg = None
        if not passed:
            failure_msg = (
                f"Multi-aggregate consistency check failed: {len(mismatches)} mismatches "
                f"out of {total_checks} checked (tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="multi_aggregate_consistency_check",
            metric_value={"mismatches": len(mismatches), "total_checked": total_checks},
            metadata={
                "source_table": self.source_table,
                "aggregates": [aggregate.__dict__ for aggregate in self.aggregates],
                "group_by": self.group_by,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "query": source_query,
                "sample_mismatches": mismatches[:10],
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
                if self.absolute_tolerance is not None:
                    return abs(target_val) <= self.absolute_tolerance
                return False

            diff_pct = abs(target_val - source_val) / abs(source_val)
            if diff_pct <= self.tolerance:
                return True
            if self.absolute_tolerance is not None:
                return abs(target_val - source_val) <= self.absolute_tolerance
            return False
        except (TypeError, ValueError):
            return target == source

    def _build_source_query(self, partition_key: str | None) -> str:
        """Build SQL query to compute source aggregates."""
        select_cols = ", ".join(self.group_by) if self.group_by else "1 as grp"
        aggregate_exprs = ", ".join(
            f"{aggregate.expression} as {aggregate.name}" for aggregate in self.aggregates
        )
        query = f"SELECT {select_cols}, {aggregate_exprs} FROM {self.source_table}"

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

    def _get_source_aggregates(
        self, context: "AssetExecutionContext", query: str
    ) -> dict[tuple, dict[str, Any]] | None:
        """Execute query to get source aggregate values."""
        try:
            if hasattr(context, "resources") and hasattr(context.resources, "trino"):
                trino = context.resources.trino
                result = trino.execute_query(query)
                if result:
                    values: dict[tuple, dict[str, Any]] = {}
                    for row in result:
                        if self.group_by:
                            key = tuple(row[: len(self.group_by)])
                            agg_values = {
                                aggregate.name: row[len(self.group_by) + idx]
                                for idx, aggregate in enumerate(self.aggregates)
                            }
                        else:
                            key = ()
                            agg_values = {
                                aggregate.name: row[idx]
                                for idx, aggregate in enumerate(self.aggregates)
                            }
                        values[key] = agg_values
                    return values

            return None
        except Exception as exc:
            if hasattr(context, "log"):
                context.log.warning(f"Failed to query source aggregates: {exc}")
            return None

    @property
    def name(self) -> str:
        return "multi_aggregate_consistency_check"


@dataclass
class ChecksumReconciliationCheck(QualityCheck):
    """
    Check that row-level hashes match between source and target tables.
    """

    source_table: str
    """Fully qualified source table name."""

    target_table: str
    """Fully qualified target table name."""

    key_columns: list[str]
    """Primary key or composite key columns used for alignment."""

    columns: list[str] | None = None
    """Columns to hash. If None, hash all non-key columns from the target table."""

    partition_column: str = "_phlo_partition_date"
    """Column used for partition filtering."""

    tolerance: float = 0.0
    """Allowed fraction of mismatches (0.0 = exact match)."""

    absolute_tolerance: int | float | None = None
    """Allowed absolute count of mismatches (None = disable)."""

    hash_algorithm: str = "xxhash64"
    """Hash algorithm to use ('xxhash64' or 'md5')."""

    float_precision: int = 6
    """Precision used when normalizing floats for hashing."""

    sample: float | None = None
    """Optional deterministic sampling fraction (0 < sample <= 1)."""

    limit: int | None = None
    """Optional limit on the number of keys compared (applies to source)."""

    def execute(self, df: pd.DataFrame, context: "AssetExecutionContext") -> QualityCheckResult:
        """Execute checksum reconciliation check."""
        missing_columns = [column for column in self.key_columns if column not in df.columns]
        if missing_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                failure_message=f"Missing key columns in target data: {missing_columns}",
            )

        if self.columns is None:
            hash_columns = [column for column in df.columns if column not in self.key_columns]
        else:
            hash_columns = self.columns

        missing_hash_columns = [column for column in hash_columns if column not in df.columns]
        if missing_hash_columns:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                failure_message=f"Missing hash columns in target data: {missing_hash_columns}",
            )

        partition_key = None
        if hasattr(context, "partition_key"):
            partition_key = context.partition_key
        elif hasattr(context, "asset_partition_key"):
            partition_key = context.asset_partition_key

        source_query = self._build_hash_query(
            self.source_table, hash_columns, partition_key, apply_limit=True
        )
        target_query = self._build_hash_query(
            self.target_table, hash_columns, partition_key, apply_limit=False
        )

        source_rows = self._get_hash_rows(context, source_query)
        if source_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                metadata={"source_table": self.source_table, "query": source_query},
                failure_message=f"Failed to query source hashes from {self.source_table}",
            )

        target_rows = self._get_hash_rows(context, target_query)
        if target_rows is None:
            return QualityCheckResult(
                passed=False,
                metric_name="checksum_reconciliation_check",
                metric_value=None,
                metadata={"target_table": self.target_table, "query": target_query},
                failure_message=f"Failed to query target hashes from {self.target_table}",
            )

        source_hashes, source_duplicates = self._rows_to_hash_map(source_rows)
        target_hashes, target_duplicates = self._rows_to_hash_map(target_rows)

        if self.limit is not None:
            target_hashes = {
                key: value for key, value in target_hashes.items() if key in source_hashes
            }

        source_keys = set(source_hashes.keys())
        target_keys = set(target_hashes.keys())

        missing_in_target = source_keys - target_keys
        missing_in_source = target_keys - source_keys

        shared_keys = source_keys.intersection(target_keys)
        hash_mismatches = {
            key for key in shared_keys if source_hashes.get(key) != target_hashes.get(key)
        }

        total_keys = len(source_keys.union(target_keys))
        duplicate_count = source_duplicates + target_duplicates
        mismatch_count = (
            len(missing_in_target)
            + len(missing_in_source)
            + len(hash_mismatches)
            + duplicate_count
        )
        total_comparable = total_keys + duplicate_count
        mismatch_pct = mismatch_count / total_comparable if total_comparable else 0.0

        passed = mismatch_pct <= self.tolerance or (
            self.absolute_tolerance is not None and mismatch_count <= self.absolute_tolerance
        )

        failure_msg = None
        if not passed:
            duplicate_segment = f", {duplicate_count} duplicate keys" if duplicate_count else ""
            failure_msg = (
                f"Checksum reconciliation failed: {len(hash_mismatches)} hash mismatches, "
                f"{len(missing_in_target)} missing in target, "
                f"{len(missing_in_source)} missing in source"
                f"{duplicate_segment} "
                f"(mismatch: {mismatch_pct:.2%}, tolerance: {self.tolerance:.2%}"
                + (
                    f", absolute_tolerance: {self.absolute_tolerance}"
                    if self.absolute_tolerance is not None
                    else ""
                )
                + ")"
            )

        return QualityCheckResult(
            passed=passed,
            metric_name="checksum_reconciliation_check",
            metric_value={
                "missing_in_target": len(missing_in_target),
                "missing_in_source": len(missing_in_source),
                "hash_mismatches": len(hash_mismatches),
                "duplicate_keys": duplicate_count,
                "total_keys": total_keys,
                "mismatch_pct": float(mismatch_pct),
            },
            metadata={
                "source_table": self.source_table,
                "target_table": self.target_table,
                "key_columns": self.key_columns,
                "hash_columns": hash_columns,
                "partition_column": self.partition_column,
                "partition_key": partition_key,
                "tolerance": self.tolerance,
                "absolute_tolerance": self.absolute_tolerance,
                "hash_algorithm": self.hash_algorithm,
                "float_precision": self.float_precision,
                "sample": self.sample,
                "limit": self.limit,
                "source_duplicates": source_duplicates,
                "target_duplicates": target_duplicates,
                "source_query": source_query,
                "target_query": target_query,
                "sample_hash_mismatches": [str(key) for key in list(hash_mismatches)[:10]],
            },
            failure_message=failure_msg,
        )

    def _build_hash_query(
        self,
        table: str,
        hash_columns: list[str],
        partition_key: str | None,
        apply_limit: bool,
    ) -> str:
        """Build SQL query to compute key + hash for a table."""
        select_cols = ", ".join(self.key_columns)
        hash_expr = self._hash_expression(hash_columns)
        query = f"SELECT {select_cols}, {hash_expr} AS row_hash FROM {table}"

        conditions = []
        if partition_key and self.partition_column:
            conditions.append(f"{self.partition_column} = '{partition_key}'")
        sampling_predicate = self._sampling_predicate()
        if sampling_predicate:
            conditions.append(sampling_predicate)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if apply_limit and self.limit is not None:
            query += f" LIMIT {self.limit}"

        return query

    def _sampling_predicate(self) -> str | None:
        """Build deterministic sampling predicate using key hash."""
        if self.sample is None:
            return None
        if self.sample <= 0 or self.sample > 1:
            raise ValueError("sample must be within (0, 1]")
        key_expr = " || '|' || ".join(
            [f"coalesce(cast({col} as varchar), '__NULL__')" for col in self.key_columns]
        )
        bucket_count = 10000
        threshold = int(self.sample * bucket_count)
        return f"mod(xxhash64({key_expr}), {bucket_count}) < {threshold}"

    def _hash_expression(self, hash_columns: list[str]) -> str:
        """Build SQL expression to compute the row hash."""
        normalized_columns = []
        for column in hash_columns:
            normalized_columns.append(
                "coalesce("
                f"cast(round(try_cast({column} as double), {self.float_precision}) as varchar), "
                f"cast({column} as varchar), "
                "'__NULL__'"
                ")"
            )
        concatenated = " || '|' || ".join(normalized_columns) if normalized_columns else "''"

        algorithm = self.hash_algorithm.lower()
        if algorithm == "xxhash64":
            return f"cast(xxhash64({concatenated}) as varchar)"
        if algorithm == "md5":
            return f"lower(to_hex(md5({concatenated})))"
        raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")

    def _get_hash_rows(self, context: "AssetExecutionContext", query: str) -> list[tuple] | None:
        """Execute query to fetch key + hash rows."""
        try:
            if hasattr(context, "resources") and hasattr(context.resources, "trino"):
                trino = context.resources.trino
                result = trino.execute_query(query)
                if result is not None:
                    return [tuple(row) for row in result]
        except Exception as exc:
            if hasattr(context, "log"):
                context.log.warning(f"Failed to query hashes: {exc}")
            return None
        return None

    def _rows_to_hash_map(self, rows: list[tuple]) -> tuple[dict[tuple, Any], int]:
        """Convert query rows to key -> hash mapping and return duplicate count."""
        hashes: dict[tuple, Any] = {}
        duplicates = 0
        for row in rows:
            key = tuple(row[:-1])
            row_hash = row[-1]
            if key not in hashes:
                hashes[key] = row_hash
            else:
                duplicates += 1
        return hashes, duplicates

    @property
    def name(self) -> str:
        return f"checksum_reconciliation_{self.source_table.replace('.', '_')}"
