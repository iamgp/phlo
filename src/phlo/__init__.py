# __init__.py - Phlo package initialization
"""
Phlo - Data Platform Framework

Declarative data pipelines with minimal boilerplate.

Usage::

    import phlo

    @phlo.quality(
        table="bronze.weather_observations",
        checks=[NullCheck(columns=["id"]), RangeCheck(column="temp", min_value=-50, max_value=60)],
    )
    def weather_quality():
        pass

    @phlo.ingestion(
        table_name="weather_observations",
        unique_key="id",
        group="weather",
    )
    def weather_ingestion(partition_date: str):
        return fetch_weather_data(partition_date)
"""

from __future__ import annotations

from typing import Any

from phlo.quality.decorator import phlo_quality as quality

ingestion: Any


# Lazy import for ingestion to avoid circular/heavy dependencies
def __getattr__(name: str) -> Any:
    if name == "ingestion":
        from phlo.ingestion.decorator import phlo_ingestion

        return phlo_ingestion
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__version__ = "0.1.0-alpha.1"
__all__ = ["ingestion", "quality"]
