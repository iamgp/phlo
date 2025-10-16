from __future__ import annotations

import multiprocessing as mp
import time
import traceback
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

import dagster as dg
from dagster.preview.freshness import FreshnessPolicy
import dlt
import requests

from lakehousekit.config import config
from lakehousekit.defs.partitions import daily_partition
from lakehousekit.dlt.ducklake_destination import (
    build_destination as ducklake_destination,
)


class PipelineTimeoutError(Exception):
    """Raised when a pipeline run exceeds its timeout."""

    pass


PIPELINE_TIMEOUT_SECONDS = 30


def _pipeline_worker(
    result_queue: mp.Queue,
    *,
    pipeline_name: str,
    dataset_name: str,
    pipelines_dir: str,
    entries: list[dict[str, Any]],
) -> None:
    """
    Execute the DLT pipeline in a separate process and communicate the result back.
    """
    start_ts = time.time()
    rows_attempted = len(entries)
    logs: list[tuple[str, str]] = []

    def record(level: str, message: str, *args: Any) -> None:
        formatted = message % args if args else message
        logs.append((level, formatted))

    record("info", f"[worker] Starting DuckLake load for pipeline '{pipeline_name}'")
    record("debug", f"[worker] Entries to load: {rows_attempted}")
    try:
        with dlt_pipeline_context(
            pipeline_name=pipeline_name,
            destination=ducklake_destination(),
            dataset_name=dataset_name,
            pipelines_dir=pipelines_dir,
        ) as pipeline:
            destination_client = getattr(pipeline, "_destination_client", None)
            record(
                "debug",
                "[worker] DLT pipeline context created; destination=%s",
                type(destination_client).__name__ if destination_client else "unknown",
            )
            runtime_config = getattr(destination_client, "runtime_config", None)
            if runtime_config:
                record(
                    "debug",
                    "[worker] DuckLake runtime: dataset=%s staging=%s "
                    "retry_count=%s backoff=%s wait_ms=%s",
                    getattr(runtime_config, "default_dataset", "unknown"),
                    getattr(runtime_config, "staging_dataset", "unknown"),
                    getattr(runtime_config, "ducklake_retry_count", "unknown"),
                    getattr(runtime_config, "ducklake_retry_backoff", "unknown"),
                    getattr(runtime_config, "ducklake_retry_wait_ms", "unknown"),
                )

            @dlt.resource(name="entries", write_disposition="append")
            def provide_entries() -> Any:
                yield entries

            record("debug", "[worker] Invoking pipeline.run for '%s'", pipeline_name)
            pipeline.run(provide_entries())
            record("info", f"[worker] pipeline.run completed for '{pipeline_name}'")

        elapsed = time.time() - start_ts
        record(
            "info",
            "[worker] DuckLake load finished in %.2fs (rows=%s)",
            elapsed,
            rows_attempted,
        )
        result_queue.put(
            {
                "status": "success",
                "rows_loaded": rows_attempted,
                "elapsed": elapsed,
                "logs": logs,
            }
        )
    except Exception as exc:  # noqa: BLE001
        record("error", f"[worker] Pipeline failed: {exc}")
        result_queue.put(
            {
                "status": "error",
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "logs": logs,
            }
        )


def run_pipeline_with_timeout(
    *,
    pipeline_name: str,
    dataset_name: str,
    pipelines_dir: str,
    entries: list[dict[str, Any]],
    timeout_seconds: int,
    context,
    partition_key: str,
) -> dict[str, Any]:
    """
    Spawn a process to run the DLT pipeline with a hard timeout.
    """
    ctx = mp.get_context("spawn")
    result_queue: mp.Queue = ctx.Queue()

    process = ctx.Process(
        target=_pipeline_worker,
        kwargs={
            "result_queue": result_queue,
            "pipeline_name": pipeline_name,
            "dataset_name": dataset_name,
            "pipelines_dir": pipelines_dir,
            "entries": entries,
        },
        name=f"dlt-pipeline-{pipeline_name}",
        daemon=True,
    )
    context.log.debug(
        "Launching DuckLake worker process for pipeline '%s' (partition %s)",
        pipeline_name,
        partition_key,
    )
    process.start()

    process.join(timeout_seconds)
    if process.is_alive():
        context.log.error(
            "Pipeline '%s' for partition %s exceeded %ss timeout; terminating process",
            pipeline_name,
            partition_key,
            timeout_seconds,
        )
        process.terminate()
        process.join(5)
        raise PipelineTimeoutError(f"Pipeline '{pipeline_name}' timed out after {timeout_seconds}s")

    if result_queue.empty():
        raise RuntimeError(f"Pipeline '{pipeline_name}' exited without returning a result")

    result = result_queue.get()

    for level, message in result.get("logs", []):
        log_method = getattr(context.log, level, context.log.info)
        try:
            log_method(message)
        except Exception:  # noqa: BLE001
            context.log.info(message)

    result.pop("logs", None)

    if result.get("status") != "success":
        error_message = result.get("error", "Unknown pipeline failure")
        tb = result.get("traceback")
        if tb:
            context.log.error("Pipeline '%s' failed with traceback:\n%s", pipeline_name, tb)
        raise RuntimeError(
            f"Pipeline execution failed for partition {partition_key}: {error_message}"
        )

    return result


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
    op_tags={"dagster/max_runtime": PIPELINE_TIMEOUT_SECONDS},
    retry_policy=dg.RetryPolicy(max_retries=3, delay=30),  # Retry 3x with 30s delay
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
    - 30-second timeout protection
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
            entries: list[dict[str, Any]] = response.json()
            context.log.info(f"Successfully fetched {len(entries)} entries from Nightscout API")
        except requests.RequestException as e:
            context.log.error(f"Failed to fetch data from Nightscout API: {e}")
            raise

        context.log.info(f"Launching DLT pipeline '{pipeline_name}' in isolated process")

        result = run_pipeline_with_timeout(
            pipeline_name=pipeline_name,
            dataset_name=config.ducklake_default_dataset,
            pipelines_dir=str(pipelines_base_dir),
            entries=entries,
            timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
            context=context,
            partition_key=partition_date,
        )

        elapsed = result["elapsed"]
        rows_loaded = result["rows_loaded"]

        context.log.info(f"Pipeline '{pipeline_name}' completed successfully in {elapsed:.2f}s")
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
        raise RuntimeError(f"Pipeline execution failed for partition {partition_date}: {e}")



