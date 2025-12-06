from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dlt
import pandas as pd
import pandera.errors
from dlt.common.pipeline import LoadInfo
from pandera.pandas import DataFrameModel

from phlo.defs.resources.iceberg import IcebergResource
from phlo.schemas.registry import TableConfig


def get_branch_from_context(context) -> str:
    """
    Extract branch name from Dagster execution context.

    Tries in order:
    1. Run tags (set by create_pipeline_branch asset)
    2. Run config (passed manually)
    3. Defaults to "main"

    Args:
        context: Dagster asset execution context

    Returns:
        Branch name to use for Iceberg operations
    """
    run_tags = context.run.tags or {}
    branch = run_tags.get("branch", None)
    if isinstance(branch, str):
        return branch
    return context.run_config.get("branch_name", "main")


def add_cascade_timestamp(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Add _cascade_ingested_at timestamp to all records.

    Args:
        records: List of dictionaries representing data records

    Returns:
        Modified list with timestamp added to each record
    """
    ingestion_timestamp = datetime.now(timezone.utc)
    for record in records:
        record["_cascade_ingested_at"] = ingestion_timestamp
    return records


def validate_with_pandera(
    context,
    data: list[dict[str, Any]],
    schema_class: type[DataFrameModel],
    column_mapping: dict[str, str] | None = None,
) -> bool:
    """
    Validate data using Pandera schema.

    Args:
        context: Dagster asset execution context for logging
        data: List of dictionaries to validate
        schema_class: Pandera DataFrameModel class for validation
        column_mapping: Optional dict to rename columns before validation

    Returns:
        True if validation passed, False if validation failed (logs warnings)
    """
    try:
        context.log.info(f"Validating {len(data)} records with {schema_class.__name__}")

        df = pd.DataFrame(data)

        if column_mapping:
            df = df.rename(columns=column_mapping)

        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    pass

        schema_class.validate(df, lazy=True)
        context.log.info(f"Validation passed for {len(df)} records")
        return True

    except pandera.errors.SchemaErrors as err:
        failure_cases = err.failure_cases
        context.log.error(f"Validation failed with {len(failure_cases)} errors")
        context.log.error(f"Validation errors:\n{failure_cases.head(10)}")
        context.log.warning("Proceeding with ingestion despite validation errors")
        return False

    except Exception as e:
        context.log.warning(f"Validation check failed with exception: {e}")
        context.log.warning("Proceeding with ingestion despite validation failure")
        return False


def setup_dlt_pipeline(
    pipeline_name: str, dataset_name: str
) -> tuple[dlt.Pipeline, Path]:
    """
    Setup DLT pipeline with filesystem destination for staging.

    Args:
        pipeline_name: Unique name for this pipeline instance
        dataset_name: Dataset name (e.g., "nightscout", "github")

    Returns:
        Tuple of (DLT pipeline, local staging root path)
    """
    pipelines_base_dir = Path.home() / ".dlt" / "pipelines" / "partitioned"
    pipelines_base_dir.mkdir(parents=True, exist_ok=True)

    local_staging_root = (pipelines_base_dir / pipeline_name / "stage").resolve()
    local_staging_root.mkdir(parents=True, exist_ok=True)

    filesystem_destination = dlt.destinations.filesystem(
        bucket_url=local_staging_root.as_uri(),
    )

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=filesystem_destination,
        dataset_name=dataset_name,
        pipelines_dir=str(pipelines_base_dir),
    )

    return pipeline, local_staging_root


def stage_to_parquet(
    context,
    pipeline: dlt.Pipeline,
    dlt_source: Any,
    local_staging_root: Path,
) -> tuple[Path, float]:
    """
    Stage data to parquet using DLT pipeline.

    Args:
        context: Dagster asset execution context for logging
        pipeline: DLT pipeline instance
        dlt_source: DLT source or resource to run
        local_staging_root: Local staging directory path

    Returns:
        Tuple of (parquet file path, elapsed time in seconds)

    Raises:
        RuntimeError: If DLT pipeline fails to produce parquet output
    """
    start_time = time.time()

    context.log.info("Staging data to parquet via DLT...")
    info: LoadInfo = pipeline.run(dlt_source, loader_file_format="parquet")

    if not info.load_packages:
        raise RuntimeError("DLT pipeline produced no load packages")

    load_package = info.load_packages[0]
    completed_jobs = load_package.jobs.get("completed_jobs") or []
    if not completed_jobs:
        raise RuntimeError("DLT pipeline completed without producing parquet output")

    parquet_files = [
        job for job in completed_jobs if job.file_path.endswith(".parquet")
    ]
    if not parquet_files:
        raise RuntimeError("DLT pipeline completed without producing parquet files")

    parquet_path = Path(parquet_files[0].file_path)
    if not parquet_path.is_absolute():
        parquet_path = (local_staging_root / parquet_path).resolve()

    elapsed = time.time() - start_time
    context.log.info(f"DLT staging completed in {elapsed:.2f}s")
    context.log.debug(f"Parquet staged to {parquet_path}")

    return parquet_path, elapsed


def merge_to_iceberg(
    context,
    iceberg: IcebergResource,
    table_config: TableConfig,
    parquet_path: Path,
    branch_name: str,
    merge_strategy: str = "merge",
    merge_config: dict[str, Any] | None = None,
) -> dict[str, int]:
    """
    Merge parquet data to Iceberg table with configurable strategy.

    Args:
        context: Dagster asset execution context for logging
        iceberg: IcebergResource instance
        table_config: TableConfig with schema and unique key
        parquet_path: Path to parquet file to merge
        branch_name: Iceberg branch/reference to use
        merge_strategy: "append" (insert-only) or "merge" (upsert). Default: "merge"
        merge_config: Configuration dict with deduplication settings

    Returns:
        Merge metrics dict with rows_inserted and rows_deleted counts
    """
    from typing import Any

    merge_config = merge_config or {}
    table_name = table_config.full_table_name

    context.log.info(
        f"Ensuring Iceberg table {table_name} exists on branch {branch_name}..."
    )
    iceberg.ensure_table(
        table_name=table_name,
        schema=table_config.iceberg_schema,
        partition_spec=table_config.partition_spec,
        override_ref=branch_name,
    )

    # Apply source deduplication if enabled
    if merge_config.get("deduplication", False):
        context.log.info("Applying source-level deduplication...")
        import pyarrow.parquet as pq

        arrow_table = pq.read_table(str(parquet_path))
        arrow_table = _deduplicate_arrow_table(
            arrow_table=arrow_table,
            unique_key=table_config.unique_key,
            method=merge_config.get("deduplication_method", "last"),
            context=context,
        )
        # Write deduplicated data back to parquet
        import tempfile

        temp_dir = tempfile.mkdtemp()
        deduped_path = Path(temp_dir) / "deduped.parquet"
        pq.write_table(arrow_table, str(deduped_path))
        parquet_path = deduped_path

    # Execute merge based on strategy
    if merge_strategy == "append":
        context.log.info(
            f"Appending data to Iceberg table on branch {branch_name}..."
        )
        merge_metrics = iceberg.append_parquet(
            table_name=table_name,
            data_path=str(parquet_path),
            override_ref=branch_name,
        )
        context.log.info(f"Appended {merge_metrics['rows_inserted']} rows to {table_name}")
    elif merge_strategy == "merge":
        context.log.info(
            f"Merging data to Iceberg table on branch {branch_name} (idempotent upsert)..."
        )
        merge_metrics = iceberg.merge_parquet(
            table_name=table_name,
            data_path=str(parquet_path),
            unique_key=table_config.unique_key,
            override_ref=branch_name,
        )
        context.log.info(
            f"Merged {merge_metrics['rows_inserted']} rows to {table_name} "
            + f"(deleted {merge_metrics['rows_deleted']} existing duplicates)"
        )
    else:
        raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    return merge_metrics


def _deduplicate_arrow_table(
    arrow_table: Any,
    unique_key: str,
    method: str,
    context: Any,
) -> Any:
    """
    Deduplicate Arrow table based on unique_key.

    Args:
        arrow_table: Input Arrow table
        unique_key: Column to deduplicate on
        method: "first" (keep first), "last" (keep last), "hash" (content-based)
        context: Dagster context for logging

    Returns:
        Deduplicated Arrow table
    """
    import pyarrow as pa

    initial_rows = len(arrow_table)

    if method == "first":
        df = arrow_table.to_pandas()
        df = df.drop_duplicates(subset=[unique_key], keep="first")
        arrow_table = pa.Table.from_pandas(df, schema=arrow_table.schema)

    elif method == "last":
        df = arrow_table.to_pandas()
        df = df.drop_duplicates(subset=[unique_key], keep="last")
        arrow_table = pa.Table.from_pandas(df, schema=arrow_table.schema)

    elif method == "hash":
        import hashlib

        df = arrow_table.to_pandas()

        def row_hash(row):
            meta_cols = {"_dlt_load_id", "_dlt_id"}
            hash_cols = [c for c in df.columns if c not in meta_cols]
            content = "|".join(str(row[c]) for c in hash_cols)
            return hashlib.md5(content.encode()).hexdigest()

        df["_content_hash"] = df.apply(row_hash, axis=1)
        df = df.drop_duplicates(subset=["_content_hash"], keep="first")
        df = df.drop(columns=["_content_hash"])
        arrow_table = pa.Table.from_pandas(df, schema=arrow_table.schema)

    final_rows = len(arrow_table)
    duplicates_removed = initial_rows - final_rows

    if duplicates_removed > 0:
        context.log.info(
            f"Source deduplication: {initial_rows} -> {final_rows} rows "
            f"({duplicates_removed} duplicates removed using method='{method}')"
        )

    return arrow_table
