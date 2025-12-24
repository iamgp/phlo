from __future__ import annotations

from dagster import DailyPartitionsDefinition

daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
