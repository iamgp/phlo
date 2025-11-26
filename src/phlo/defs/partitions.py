# partitions.py - Partitioning configuration for Dagster assets
# Defines how time-series data is partitioned for efficient processing

from __future__ import annotations

from dagster import DailyPartitionsDefinition

# Daily partitions for time-series data
# Adjust start_date to the earliest data in your system
daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
