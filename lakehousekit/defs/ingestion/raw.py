from __future__ import annotations

from dagster import AssetExecutionContext, asset

from lakehousekit.config import config
from lakehousekit.schemas import RawDataOutput

RAW_BIOREACTOR_PATH = config.raw_bioreactor_path_obj


@asset(
    group_name="raw_ingestion",
    description="Raw bioreactor parquet files from Airbyte ingestion",
)
def raw_bioreactor_data(context: AssetExecutionContext) -> RawDataOutput:
    """Materialised bioreactor parquet files placed in the raw lake."""

    raw_path = RAW_BIOREACTOR_PATH

    if not raw_path.exists():
        context.log.warning("Raw data path does not exist: %s", raw_path)
        return RawDataOutput(status="no_data", path=str(raw_path))

    files = sorted(file.name for file in raw_path.glob("*.parquet"))
    context.log.info("Found %d parquet files", len(files))

    return RawDataOutput(
        status="available",
        path=str(raw_path),
        file_count=len(files),
        files=files[:10],
    )
