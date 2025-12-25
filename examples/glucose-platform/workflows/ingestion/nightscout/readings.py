"""Nightscout glucose entries ingestion workflow.

Replicates the example from workflows.ingestion.nightscout.glucose
"""

from __future__ import annotations

from dlt.sources.rest_api import rest_api
from phlo_dlt import phlo_ingestion

from workflows.schemas.nightscout import RawGlucoseEntries


@phlo_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    validation_schema=RawGlucoseEntries,
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
    merge_strategy="merge",
    merge_config={"deduplication_method": "last"},
)
def glucose_entries(partition_date: str):
    """
    Ingest Nightscout glucose entries using DLT rest_api source.

    Fetches CGM glucose readings from the Nightscout API for a specific partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Merge strategy: Upsert mode with deduplication (keeps most recent reading)
    - Deduplication based on _id field (Nightscout's unique entry ID)
    - Daily partitioning by timestamp
    - Automatic validation with Pandera schema
    - Branch-aware writes to Iceberg

    Why merge strategy?
    - API may return overlapping data when querying time windows
    - Nightscout allows retroactive corrections to glucose readings
    - Running the same partition multiple times must be idempotent
    - "last" dedup strategy keeps most recent reading if duplicates exist

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource for glucose entries, or None if no data
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    return rest_api(
        client={
            "base_url": "https://gwp-diabetes.fly.dev/api/v1",
        },
        resources=[
            {
                "name": "entries",
                "endpoint": {
                    "path": "entries.json",
                    "params": {
                        "count": 10000,
                        "find[dateString][$gte]": start_time_iso,
                        "find[dateString][$lt]": end_time_iso,
                    },
                },
            }
        ],
    )
