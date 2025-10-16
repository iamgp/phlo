from __future__ import annotations

from dagster import DailyPartitionsDefinition

# Daily partitions for time-series glucose data
# Start date should be adjusted to the earliest data in your system
daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
