# partitions.py - Partitioning configuration for Dagster assets
# Defines how time-series data is partitioned for efficient processing
# and querying of glucose readings by date

from __future__ import annotations

from dagster import DailyPartitionsDefinition

# --- Partition Definitions ---
# Time-based partitioning for asset materialization
# Daily partitions for time-series glucose data
# Start date should be adjusted to the earliest data in your system
daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
