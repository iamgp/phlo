"""Shared partition definitions for phlo-dagster assets.

This module provides standard partition definitions used across Phlo's
Dagster-based orchestration layer. Partitions enable time-based slicing
of data assets for incremental processing and backfills.

Partition Types:
    - daily_partition: Daily date-based partitioning starting from 2025-01-01
      using Europe/London timezone for business-day alignment.

Usage:
    Partitions are typically referenced in asset specs and applied to
    ingestion and transformation assets that process data incrementally.

Example:
    Using the daily partition in an asset spec::

        from phlo_dagster.partitions import daily_partition
        from phlo.capabilities import AssetSpec

        spec = AssetSpec(
            key="raw.orders",
            partitions=daily_partition,
            # ... other configuration
        )

"""

from __future__ import annotations

from dagster import DailyPartitionsDefinition

# Default daily partitioning for ingestion/materialization assets.
daily_partition = DailyPartitionsDefinition(
    start_date="2025-01-01",
    timezone="Europe/London",
)
