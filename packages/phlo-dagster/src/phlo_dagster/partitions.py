"""Shared partition definitions for phlo Dagster assets."""

from __future__ import annotations

from dagster import DailyPartitionsDefinition

# Default daily partitioning for ingestion/materialization assets.
daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
