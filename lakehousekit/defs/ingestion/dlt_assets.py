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

            # Try multiple paths to get row count
            rows_loaded = 0
            if hasattr(info, "metrics") and info.metrics:
                # Try different metric paths
                rows_loaded = (
                    info.metrics.get("data", {}).get("rows", 0)
                    or info.metrics.get("rows_loaded", 0)
                    or sum(
                        load.get("rows_loaded", 0)
                        for load in info.metrics.get("loads", [])
                    )
                )

            # Fallback: check load packages
            if rows_loaded == 0 and hasattr(info, "load_packages"):
                for package in info.load_packages:
                    if hasattr(package, "state") and package.state == "loaded":
                        context.log.debug(f"Package jobs: {package.jobs}")
                        for job_name, job in package.jobs.items():
                            if hasattr(job, "metrics"):
                                rows_loaded += job.metrics.get("rows_loaded", 0)

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
