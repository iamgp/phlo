from dagster import asset, AssetExecutionContext, AssetIn
import os

@asset(
    group_name="raw_ingestion",
    description="Raw bioreactor parquet files from Airbyte ingestion",
)
def raw_bioreactor_data(context: AssetExecutionContext):
    """
    Represents raw parquet files landed in /data/lake/raw/bioreactor/
    This asset is materialized by Airbyte connections.

    In practice, this could check MinIO/S3 for file presence or count.
    """
    raw_path = "/data/lake/raw/bioreactor"

    if not os.path.exists(raw_path):
        context.log.warning(f"Raw data path does not exist: {raw_path}")
        return {"status": "no_data", "path": raw_path}

    files = [f for f in os.listdir(raw_path) if f.endswith('.parquet')]
    context.log.info(f"Found {len(files)} parquet files in {raw_path}")

    return {
        "status": "available",
        "path": raw_path,
        "file_count": len(files),
        "files": files[:10],  # First 10 for logging
    }
