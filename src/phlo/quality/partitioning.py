from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class PartitionScope:
    partition_key: str | None
    partition_column: str
    rolling_window_days: int | None
    full_table: bool


def get_partition_key(context: object) -> str | None:
    partition_key = getattr(context, "partition_key", None)
    if isinstance(partition_key, str) and partition_key:
        return partition_key

    asset_partition_key = getattr(context, "asset_partition_key", None)
    if isinstance(asset_partition_key, str) and asset_partition_key:
        return asset_partition_key

    return None


def apply_partition_scope(sql: str, *, scope: PartitionScope) -> str:
    if scope.full_table:
        return sql

    if scope.partition_key is not None:
        return _append_where(sql, f"{scope.partition_column} = '{scope.partition_key}'")

    if scope.rolling_window_days is None:
        return sql

    cutoff = date.today() - timedelta(days=scope.rolling_window_days)
    return _append_where(sql, f"{scope.partition_column} >= '{cutoff.isoformat()}'")


def _append_where(sql: str, condition: str) -> str:
    if "where" in sql.lower():
        return f"{sql}\nAND {condition}"
    return f"{sql}\nWHERE {condition}"
