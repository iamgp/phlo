from __future__ import annotations

import os

from dagster import asset


@asset(
    group_name="raw_ingestion",
    description="Raw bioreactor parquet files from Airbyte ingestion",
)
def raw_bioreactor_data(context):
    """Materialised bioreactor parquet files placed in the raw lake."""

    raw_path = "/data/lake/raw/bioreactor"

    if not os.path.exists(raw_path):
        context.log.warning("Raw data path does not exist: %s", raw_path)
        return {"status": "no_data", "path": raw_path}

    files = [name for name in os.listdir(raw_path) if name.endswith(".parquet")]
    context.log.info("Found %d parquet files", len(files))

    return {
        "status": "available",
        "path": raw_path,
        "file_count": len(files),
        "files": files[:10],
    }
