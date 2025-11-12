from __future__ import annotations

from dlt.sources.rest_api import rest_api

from cascade.iceberg.schema import NIGHTSCOUT_ENTRIES_SCHEMA
from cascade.ingestion import cascade_ingestion
from cascade.schemas.glucose import RawGlucoseEntries


@cascade_ingestion(
    table_name="glucose_entries",
    unique_key="_id",
    iceberg_schema=NIGHTSCOUT_ENTRIES_SCHEMA,
    validation_schema=RawGlucoseEntries,
    group="nightscout",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def glucose_entries(partition_date: str):
    """
    Ingest Nightscout glucose entries using DLT rest_api source.

    Fetches CGM glucose readings from the Nightscout API for a specific partition date,
    stages to parquet, and merges to Iceberg with idempotent deduplication.

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Deduplication based on _id field (Nightscout's unique entry ID)
    - Daily partitioning by timestamp
    - Automatic validation with Pandera schema
    - Branch-aware writes to Iceberg

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT resource for glucose entries, or None if no data
    """
    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    source = rest_api(  # type: ignore[arg-type]
        {
            "client": {
                "base_url": "https://gwp-diabetes.fly.dev/api/v1",
            },
            "resources": [
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
        }
    )

    return source
