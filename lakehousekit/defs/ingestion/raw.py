from __future__ import annotations

import os

from pathlib import Path
from typing import Any, Dict

from dagster import AssetExecutionContext, asset

RAW_BIOREACTOR_PATH = Path(
    os.getenv("RAW_BIOREACTOR_PATH", "/data/lake/raw/bioreactor")
)


@asset(
    group_name="raw_ingestion",
    description="Raw bioreactor parquet files from Airbyte ingestion",
)
def raw_bioreactor_data(context: AssetExecutionContext) -> Dict[str, Any]:
    """Materialised bioreactor parquet files placed in the raw lake."""

    raw_path = RAW_BIOREACTOR_PATH

    if not raw_path.exists():
        context.log.warning("Raw data path does not exist: %s", raw_path)
        return {"status": "no_data", "path": str(raw_path)}

    files = sorted(file.name for file in raw_path.glob("*.parquet"))
    context.log.info("Found %d parquet files", len(files))

    return {
        "status": "available",
        "path": str(raw_path),
        "file_count": len(files),
        "files": files[:10],
    }
