"""Lightweight Delta Lake helper utilities.

The functions in this module wrap :mod:`phlo_delta.tables` without importing
the optional Delta runtime until a helper is called.
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa


def table_exists(table_name: str, storage_options: dict[str, str] | None = None) -> bool:
    """Return whether a Delta table can be opened."""
    from phlo_delta.tables import _default_storage_options, _load_deltalake, _resolve_table_uri

    delta_table_cls, _write_deltalake = _load_deltalake()
    try:
        delta_table_cls(
            _resolve_table_uri(table_name),
            storage_options=_default_storage_options(storage_options),
        )
    except Exception:
        return False
    return True


def load_table_schema(
    table_name: str,
    storage_options: dict[str, str] | None = None,
) -> pa.Schema:
    """Load a Delta table schema as a PyArrow schema."""
    from phlo_delta.tables import _default_storage_options, _load_deltalake, _resolve_table_uri

    delta_table_cls, _write_deltalake = _load_deltalake()
    table = delta_table_cls(
        _resolve_table_uri(table_name),
        storage_options=_default_storage_options(storage_options),
    )
    return table.schema().to_pyarrow()


def identity_partition(*columns: str) -> list[str]:
    """Build Delta partition columns from identity-partitioned columns."""
    return list(columns)


def maintenance_recommendations(
    stats: dict[str, Any],
    *,
    max_file_count: int = 1000,
    min_avg_file_size_mb: float = 32.0,
) -> list[str]:
    """Return conservative maintenance recommendations from Delta table stats."""
    recommendations: list[str] = []
    file_count = int(stats.get("file_count") or 0)
    total_size_mb = float(stats.get("total_size_mb") or 0.0)
    avg_file_size_mb = total_size_mb / file_count if file_count else 0.0

    if file_count > max_file_count:
        recommendations.append("vacuum")
    if file_count > 1 and avg_file_size_mb < min_avg_file_size_mb:
        recommendations.append("consider_optimize")

    return recommendations


def recommend_table_maintenance(
    table_name: str,
    storage_options: dict[str, str] | None = None,
    **kwargs: Any,
) -> list[str]:
    """Load Delta table stats and return maintenance recommendations."""
    from phlo_delta.tables import get_table_stats

    return maintenance_recommendations(
        get_table_stats(table_name, storage_options=storage_options),
        **kwargs,
    )


__all__ = [
    "identity_partition",
    "load_table_schema",
    "maintenance_recommendations",
    "recommend_table_maintenance",
    "table_exists",
]
