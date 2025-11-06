# dlt_assets.py - Dagster assets for ingesting Nightscout glucose data using DLT (Data Load Tool)
# Implements the raw data ingestion layer of the lakehouse, fetching from Nightscout API
# and staging data to S3 parquet files, then registering in Iceberg tables

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import dagster as dg
import dlt
import requests
from dagster.preview.freshness import FreshnessPolicy


from cascade.config import config
from cascade.defs.partitions import daily_partition
from cascade.defs.resources.iceberg import IcebergResource
from cascade.iceberg.schema import get_schema, get_unique_key


# --- Helper Functions ---
# Utility functions for staging path generation and data processing
def get_staging_path(partition_date: str, table_name: str) -> str:
    """
    Get S3 staging path for a partition.

    Args:
        partition_date: Partition date (YYYY-MM-DD)
        table_name: Table name (e.g., "entries", "treatments")

    Returns:
        S3 path for staging parquet files
    """
    return f"{config.iceberg_staging_path}/{table_name}/{partition_date}"


# --- Dagster Assets ---
# Data ingestion assets that materialize raw data into the lakehouse
@dg.asset(
    name="dlt_glucose_entries",
    group_name="nightscout",
    partitions_def=daily_partition,
    description=(
        "Nightscout CGM glucose entries ingested via DLT to S3 parquet, "
        "then merged to Iceberg raw.entries with idempotent deduplication. "
        "Safe to run multiple times - uses _id as unique key."
    ),
    compute_kind="dlt+pyiceberg",
    op_tags={"dagster/max_runtime": 300},
    retry_policy=dg.RetryPolicy(max_retries=3, delay=30),
    automation_condition=dg.AutomationCondition.on_cron("0 */1 * * *"),
    freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=24), warn_window=timedelta(hours=1)),
)
def entries(context, iceberg: IcebergResource) -> dg.MaterializeResult:
    """
    Ingest Nightscout entries using two-step pattern with idempotent merge:

    1. DLT stages data to S3 as parquet files
    2. PyIceberg merges to Iceberg table with deduplication

    Features:
    - Idempotent ingestion: safe to run multiple times without duplicates
    - Deduplication based on _id field (Nightscout's unique entry ID)
    - Daily partitioning by timestamp
    - S3 parquet staging with filesystem destination
    - Iceberg table management with schema enforcement
    - Comprehensive error handling and logging
    """
    partition_date = context.partition_key
    pipeline_name = f"nightscout_entries_{partition_date.replace('-', '_')}"
    table_name = f"{config.iceberg_default_namespace}.glucose_entries"

    start_time_iso = f"{partition_date}T00:00:00.000Z"
    end_time_iso = f"{partition_date}T23:59:59.999Z"

    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    context.log.info(f"Starting ingestion for partition {partition_date}")
    context.log.info(f"Date range: {start_time_iso} to {end_time_iso}")
    context.log.info(f"Target table: {table_name}")

    try:
        # Step 1: Fetch data from Nightscout API
        context.log.info("Fetching data from Nightscout API...")
        try:
            response = requests.get(
                "https://gwp-diabetes.fly.dev/api/v1/entries.json",
                params={
                    "count": "10000",
                    "find[dateString][$gte]": start_time_iso,
                    "find[dateString][$lt]": end_time_iso,
                },
                timeout=30,
            )
            response.raise_for_status()
            entries_data: list[dict[str, Any]] = response.json()
            context.log.info(f"Successfully fetched {len(entries_data)} entries from API")
        except requests.RequestException as e:
            context.log.error(f"Failed to fetch data from Nightscout API: {e}")
            raise

        if not entries_data:
            context.log.info(f"No data for partition {partition_date}, skipping")
            return dg.MaterializeResult(
                metadata={
                    "partition_date": dg.MetadataValue.text(partition_date),
                    "rows_loaded": dg.MetadataValue.int(0),
                    "status": dg.MetadataValue.text("no_data"),
                }
            )

        # Add cascade ingestion timestamp
        ingestion_timestamp = datetime.now(timezone.utc)
        for entry in entries_data:
            entry["_cascade_ingested_at"] = ingestion_timestamp

        # Step 2: Stage to S3 parquet using DLT
        context.log.info("Staging data to parquet via DLT...")
        start_time_ts = time.time()

        staging_path = get_staging_path(partition_date, "entries")
        local_staging_root = (pipelines_base_dir / pipeline_name / "stage").resolve()
        local_staging_root.mkdir(parents=True, exist_ok=True)

        # Create DLT pipeline with filesystem destination targeting local staging
        filesystem_destination = dlt.destinations.filesystem(
            bucket_url=local_staging_root.as_uri(),
        )

        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination=filesystem_destination,
            dataset_name="nightscout",
            pipelines_dir=str(pipelines_base_dir),
        )

        @dlt.resource(name="entries", write_disposition="replace")
        def provide_entries() -> Any:
            yield entries_data

        # Run DLT pipeline to stage parquet files
        info = pipeline.run(
            provide_entries(),
            loader_file_format="parquet",
        )

        if not info.load_packages:
            raise RuntimeError("DLT pipeline produced no load packages")

        load_package = info.load_packages[0]
        completed_jobs = load_package.jobs.get("completed_jobs") or []
        if not completed_jobs:
            raise RuntimeError("DLT pipeline completed without producing parquet output")

        # Filter for actual parquet files (exclude pipeline state and other files)
        parquet_files = [job for job in completed_jobs if job.file_path.endswith('.parquet')]
        if not parquet_files:
            raise RuntimeError("DLT pipeline completed without producing parquet files")

        parquet_path = Path(parquet_files[0].file_path)
        if not parquet_path.is_absolute():
            parquet_path = (local_staging_root / parquet_path).resolve()

        context.log.debug(
            "DLT staged parquet to %s (logical %s)",
            parquet_path,
            staging_path,
        )

        dlt_elapsed = time.time() - start_time_ts
        context.log.info(f"DLT staging completed in {dlt_elapsed:.2f}s")

        # Step 3: Ensure Iceberg table exists
        context.log.info(f"Ensuring Iceberg table {table_name} exists...")
        schema = get_schema("entries")
        iceberg.ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=None,
        )

        # Step 4: Merge to Iceberg table (idempotent ingestion)
        context.log.info("Merging data to Iceberg table (idempotent upsert)...")
        unique_key = get_unique_key("entries")
        merge_metrics = iceberg.merge_parquet(
            table_name=table_name,
            data_path=str(parquet_path),
            unique_key=unique_key,
        )

        total_elapsed = time.time() - start_time_ts
        rows_loaded = len(entries_data)
        context.log.info(f"Ingestion completed successfully in {total_elapsed:.2f}s")
        context.log.info(
            f"Merged {merge_metrics['rows_inserted']} rows to {table_name} "
            f"(deleted {merge_metrics['rows_deleted']} existing duplicates)"
        )

        return dg.MaterializeResult(
            metadata={
                "partition_date": dg.MetadataValue.text(partition_date),
                "rows_loaded": dg.MetadataValue.int(rows_loaded),
                "rows_inserted": dg.MetadataValue.int(merge_metrics["rows_inserted"]),
                "rows_deleted": dg.MetadataValue.int(merge_metrics["rows_deleted"]),
                "unique_key": dg.MetadataValue.text(unique_key),
                "start_time": dg.MetadataValue.text(start_time_iso),
                "end_time": dg.MetadataValue.text(end_time_iso),
                "table_name": dg.MetadataValue.text(table_name),
                "dlt_elapsed_seconds": dg.MetadataValue.float(dlt_elapsed),
                "total_elapsed_seconds": dg.MetadataValue.float(total_elapsed),
            }
        )

    except requests.RequestException as e:
        context.log.error(f"API request failed for partition {partition_date}: {e}")
        raise RuntimeError(
            f"Failed to fetch data from Nightscout API for partition {partition_date}"
        ) from e

    except Exception as e:
        context.log.error(f"Ingestion failed for partition {partition_date}: {e}")
        raise RuntimeError(f"Ingestion failed for partition {partition_date}: {e}") from e
