from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class PartitionScope:
    """Partition filter scope for SQL quality checks.

    Attributes:
        partition_key: Explicit partition key to target, if available.
        partition_column: Column name used for partition filtering.
        rolling_window_days: Optional rolling lookback window in days.
        full_table: If ``True``, skip partition filtering.
    """

    partition_key: str | None
    partition_column: str
    rolling_window_days: int | None
    full_table: bool


def get_partition_key(context: object) -> str | None:
    """Extract a partition key from a Dagster-like execution context.

    Args:
        context: Context object exposing partition key attributes.

    Returns:
        Partition key value when available, otherwise ``None``.
    """

    partition_key = getattr(context, "partition_key", None)
    if isinstance(partition_key, str) and partition_key:
        return partition_key

    asset_partition_key = getattr(context, "asset_partition_key", None)
    if isinstance(asset_partition_key, str) and asset_partition_key:
        return asset_partition_key

    return None


def apply_partition_scope(sql: str, *, scope: PartitionScope) -> str:
    """Apply partition scope predicates to a SQL statement.

    Args:
        sql: Base SQL statement.
        scope: Partition filtering configuration.

    Returns:
        SQL statement with appended partition predicates when required.
    """

    if scope.full_table:
        return sql

    if scope.partition_key is not None:
        return _append_where(
            sql, f"{scope.partition_column} = {_date_literal(scope.partition_key)}"
        )

    if scope.rolling_window_days is None:
        return sql

    cutoff = date.today() - timedelta(days=scope.rolling_window_days)
    return _append_where(sql, f"{scope.partition_column} >= {_date_literal(cutoff.isoformat())}")


def _date_literal(value: str) -> str:
    """Format a SQL date literal.

    Args:
        value: ISO date string.

    Returns:
        SQL date literal expression.
    """

    return f"DATE '{value}'"


def _append_where(sql: str, condition: str) -> str:
    """Append a condition to SQL with ``WHERE`` or ``AND``.

    Args:
        sql: Base SQL statement.
        condition: SQL predicate expression.

    Returns:
        SQL statement with appended predicate.
    """

    if "where" in sql.lower():
        return f"{sql}\nAND {condition}"
    return f"{sql}\nWHERE {condition}"
