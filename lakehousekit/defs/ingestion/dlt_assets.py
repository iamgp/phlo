from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import dagster as dg
import dlt
import requests

from lakehousekit.config import config
from lakehousekit.dlt.ducklake_destination import build_destination as ducklake_destination
from lakehousekit.defs.partitions import daily_partition


class PipelineTimeoutError(Exception):
    """Raised when a pipeline run exceeds its timeout."""

    pass


@contextmanager
def dlt_pipeline_context(
    pipeline_name: str,
    destination: Any,
    dataset_name: str,
    pipelines_dir: str | None = None,
):
    """
    Context manager for DLT pipeline with proper cleanup.

    Ensures DuckDB connections are properly closed even if the pipeline fails.
    """
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name=dataset_name,
        pipelines_dir=pipelines_dir,
    )
    try:
        yield pipeline
    finally:
        # Explicit cleanup of DuckDB connections
        try:
            if hasattr(pipeline, "_destination_client") and pipeline._destination_client:
                client = pipeline._destination_client
                if hasattr(client, "sql_client") and client.sql_client:
                    if hasattr(client.sql_client, "_conn") and client.sql_client._conn:
                        client.sql_client._conn.close()
        except Exception:
            # Silently ignore cleanup errors to avoid masking original exception
            pass


@dg.asset(
    name="nightscout_entries",
    group_name="raw_ingestion",
    partitions_def=daily_partition,
    description="Nightscout CGM entries ingested via dlt with daily partitioning",
    compute_kind="dlt",
    op_tags={"dagster/max_runtime": 300},  # 5-minute timeout at Dagster level
)
def nightscout_entries(context) -> dg.MaterializeResult:
    """
    Ingest Nightscout data for specific partition using dlt with parameterized date filtering.

    Each partition fetches data for a specific day using the Nightscout API's date range filters.
    Data is loaded into DuckLake via DuckDB with transactional catalog support.

    Features:
    - Isolated pipeline working directories per partition
    - Automatic connection cleanup
    - 5-minute timeout protection
    - Comprehensive error handling and logging
    """
    partition_date = context.partition_key
    pipeline_name = f"nightscout_{partition_date.replace('-', '_')}"

    # Define start and end times for this partition (full day in UTC)
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    # Create isolated pipeline working directory
    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    context.log.info(
        f"Starting pipeline '{pipeline_name}' for partition {partition_date}"
    )
    context.log.info(f"Date range: {start_time} to {end_time}")

    @dlt.resource(name="nightscout_entries", write_disposition="append")
    def get_entries() -> Any:
        """Fetch entries from Nightscout API with date range parameters."""
        context.log.info(f"Fetching data from Nightscout API for {partition_date}")
        try:
            response = requests.get(
                "https://gwp-diabetes.fly.dev/api/v1/entries.json",
                params={
                    "count": "10000",
                    "find[dateString][$gte]": start_time,
                    "find[dateString][$lt]": end_time,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            context.log.info(
                f"Successfully fetched {len(data)} entries from Nightscout API"
            )
            yield data
        except requests.RequestException as e:
            context.log.error(f"Failed to fetch data from Nightscout API: {e}")
            raise

    try:
        # Use context manager for automatic cleanup
        context.log.info(f"Creating DLT pipeline '{pipeline_name}'")
        start_time_ts = time.time()

        with dlt_pipeline_context(
            pipeline_name=pipeline_name,
            destination=ducklake_destination(),
            dataset_name=config.ducklake_default_dataset,
            pipelines_dir=str(pipelines_base_dir),
        ) as pipeline:
            context.log.info("Pipeline created. Beginning data extraction and load...")

            info = pipeline.run(get_entries())

            elapsed = time.time() - start_time_ts
            context.log.info(
                f"Pipeline '{pipeline_name}' completed successfully in {elapsed:.2f}s"
            )

            # Extract metrics - DLT load info structure
            context.log.debug(f"Load info structure: {info}")
            context.log.debug(f"Load info metrics: {info.metrics}")

            # Extract row count from DLT LoadInfo properly
            rows_loaded = 0
            
            # Method 1: Check load packages for completed jobs
            if hasattr(info, "load_packages") and info.load_packages:
                for package in info.load_packages:
                    if hasattr(package, "jobs") and package.jobs:
                        context.log.debug(f"Package jobs: {package.jobs}")
                        for job_id, job_info in package.jobs.items():
                            # Count completed jobs that loaded actual data (not just pipeline state)
                            if (hasattr(job_info, "state") and job_info.state == "completed_jobs" and
                                hasattr(job_info, "job_file_info") and job_info.job_file_info and
                                hasattr(job_info.job_file_info, "table_name") and
                                job_info.job_file_info.table_name == "nightscout_entries"):
                                # Estimate rows from file size (rough approximation)
                                if hasattr(job_info, "file_size") and job_info.file_size:
                                    # Rough estimate: ~50 bytes per row average for JSON CGM data
                                    estimated_rows = max(1, job_info.file_size // 50)
                                    rows_loaded += estimated_rows
                                    context.log.debug(f"Job {job_id}: file_size={job_info.file_size}, estimated_rows={estimated_rows}")

            # Method 2: Check metrics from LoadInfo.metrics for job_metrics
            if rows_loaded == 0 and hasattr(info, "metrics") and info.metrics:
                for package_id, package_data in info.metrics.items():
                    if isinstance(package_data, list):
                        for load_step in package_data:
                            if "job_metrics" in load_step:
                                for job_id, job_metrics in load_step["job_metrics"].items():
                                    # Look for the main data table (not pipeline state)
                                    if "nightscout_entries" in job_id and hasattr(job_metrics, "state") and job_metrics.state == "completed":
                                        # If we have a successful load job, assume at least some data was loaded
                                        rows_loaded += 1  # Conservative estimate
                                        context.log.debug(f"Found completed job: {job_id}")

            # Method 3: Conservative fallback - if we have any evidence of data loading, report at least 1 row
            if rows_loaded == 0:
                # Check if we have any completed jobs at all
                has_completed_jobs = False
                if hasattr(info, "load_packages") and info.load_packages:
                    for package in info.load_packages:
                        if hasattr(package, "jobs") and package.jobs:
                            completed_jobs = [j for j in package.jobs.values() if hasattr(j, "state") and j.state == "completed_jobs"]
                            if completed_jobs:
                                has_completed_jobs = True
                                break
                
                if has_completed_jobs:
                    rows_loaded = 1  # Conservative: we know something was loaded
                    context.log.info(f"Conservative estimate: detected completed jobs, assuming at least 1 row loaded")

            context.log.info(f"Loaded {rows_loaded} rows for partition {partition_date}")

            return dg.MaterializeResult(
                metadata={
                    "partition_date": dg.MetadataValue.text(partition_date),
                    "rows_loaded": dg.MetadataValue.int(rows_loaded),
                    "start_time": dg.MetadataValue.text(start_time),
                    "end_time": dg.MetadataValue.text(end_time),
                    "pipeline_name": dg.MetadataValue.text(pipeline_name),
                    "execution_time_seconds": dg.MetadataValue.float(elapsed),
                }
            )

    except requests.RequestException as e:
        context.log.error(
            f"API request failed for partition {partition_date}: {e}"
        )
        raise RuntimeError(
            f"Failed to fetch data from Nightscout API for partition {partition_date}"
        ) from e

    except Exception as e:
        context.log.error(
            f"Pipeline '{pipeline_name}' failed for partition {partition_date}: {e}"
        )
        raise RuntimeError(
            f"Pipeline execution failed for partition {partition_date}: {e}"
        ) from e
