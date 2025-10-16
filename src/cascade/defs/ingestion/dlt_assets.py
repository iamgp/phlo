from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

import dagster as dg
from dagster.preview.freshness import FreshnessPolicy
import dlt
import requests

from cascade.config import config
from cascade.defs.partitions import daily_partition
from cascade.dlt.ducklake_destination import (
    build_destination as ducklake_destination,
)


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
        try:
            if (
                hasattr(pipeline, "_destination_client")
                and pipeline._destination_client
                and hasattr(pipeline._destination_client, "sql_client")
                and pipeline._destination_client.sql_client
                and hasattr(pipeline._destination_client.sql_client, "_conn")
                and pipeline._destination_client.sql_client._conn
            ):
                pipeline._destination_client.sql_client._conn.close()
        except Exception:
            pass


@dg.asset(
    name="entries",
    group_name="ingestion",
    partitions_def=daily_partition,
    description=(
        "Nightscout CGM entries ingested via DLT into DuckLake bronze.entries "
        "with daily partitioning"
    ),
    compute_kind="dlt",
    op_tags={"dagster/max_runtime": 300},
    retry_policy=dg.RetryPolicy(max_retries=3, delay=30),
    automation_condition=dg.AutomationCondition.on_cron("0 */1 * * *"),
    freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=1)),
)
def entries(context) -> dg.MaterializeResult:
    """
    Ingest Nightscout data for specific partition using dlt with parameterized date filtering.

    Each partition fetches data for a specific day using the Nightscout API's date range filters.
    Data is loaded into DuckLake via DuckDB with transactional catalog support.

    Features:
    - Isolated pipeline working directories per partition
    - Automatic connection cleanup
    - Comprehensive error handling and logging
    """
    partition_date = context.partition_key
    pipeline_name = f"nightscout_{partition_date.replace('-', '_')}"

    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    context.log.info(f"Starting pipeline '{pipeline_name}' for partition {partition_date}")
    context.log.info(f"Date range: {start_time} to {end_time}")

    try:
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
            entries_data: list[dict[str, Any]] = response.json()
            context.log.info(f"Successfully fetched {len(entries_data)} entries from Nightscout API")
        except requests.RequestException as e:
            context.log.error(f"Failed to fetch data from Nightscout API: {e}")
            raise

        context.log.info(f"Creating DLT pipeline '{pipeline_name}'")
        start_time_ts = time.time()

        with dlt_pipeline_context(
            pipeline_name=pipeline_name,
            destination=ducklake_destination(),
            dataset_name=config.ducklake_default_dataset,
            pipelines_dir=str(pipelines_base_dir),
        ) as pipeline:
            context.log.info("Pipeline created. Beginning data extraction and load...")

            @dlt.resource(name="entries", write_disposition="append")
            def provide_entries() -> Any:
                yield entries_data

            info = pipeline.run(provide_entries())

            elapsed = time.time() - start_time_ts
            context.log.info(f"Pipeline '{pipeline_name}' completed successfully in {elapsed:.2f}s")

            rows_loaded = len(entries_data)
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
        context.log.error(f"API request failed for partition {partition_date}: {e}")
        raise RuntimeError(
            f"Failed to fetch data from Nightscout API for partition {partition_date}"
        ) from e

    except Exception as e:
        context.log.error(f"Pipeline '{pipeline_name}' failed for partition {partition_date}: {e}")
        raise RuntimeError(
            f"Pipeline execution failed for partition {partition_date}: {e}"
        ) from e
