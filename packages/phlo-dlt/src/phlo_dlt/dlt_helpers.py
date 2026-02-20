"""Shared helper utilities for DLT ingestion execution."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dlt
import pandas as pd
import pandera.errors
import ulid
from dlt.common.pipeline import LoadInfo
from pandera.engines import pandas_engine
from pandera.pandas import DataFrameModel
from phlo.capabilities.interfaces import TableStore
from phlo.logging import get_logger

from phlo_dlt.registry import TableConfig

logger = get_logger(__name__)


def generate_row_id() -> str:
    """Return a globally unique row identifier for ingestion metadata."""
    return str(ulid.ULID())


def get_branch_from_context(context: Any) -> str:
    """Return the target branch from Dagster context tags.

    Args:
        context: Dagster execution context or compatible object exposing ``tags``.

    Returns:
        Branch name from ``context.tags["branch"]`` when present, else ``"main"``.
    """

    tags = getattr(context, "tags", None) or {}
    branch = tags.get("branch")
    if isinstance(branch, str) and branch:
        return branch

    return "main"


def inject_metadata_columns(
    parquet_path: Path,
    partition_date: str,
    run_id: str,
    context: Any = None,
) -> Path:
    """Append Phlo metadata columns to a staged parquet file.

    Args:
        parquet_path: Absolute path to the parquet file to mutate.
        partition_date: Partition date associated with this ingestion run.
        run_id: Orchestrator run identifier.
        context: Optional Dagster context used for structured logging.

    Returns:
        The same parquet path after metadata columns are written.
    """

    import pyarrow as pa
    import pyarrow.parquet as pq

    arrow_table = pq.read_table(str(parquet_path))
    num_rows = len(arrow_table)
    logger.info(
        "dlt_metadata_injection_started",
        parquet_path=str(parquet_path),
        row_count=num_rows,
    )

    if context:
        context.log.info(f"Injecting metadata columns into {num_rows} rows")

    ingested_at = datetime.now(timezone.utc)

    row_ids = [generate_row_id() for _ in range(num_rows)]
    row_id_col = pa.array(row_ids, type=pa.string())

    ingested_at_col = pa.array([ingested_at] * num_rows, type=pa.timestamp("us"))
    partition_date_col = pa.array([partition_date] * num_rows, type=pa.string())
    run_id_col = pa.array([run_id] * num_rows, type=pa.string())

    arrow_table = arrow_table.append_column("_phlo_row_id", row_id_col)
    arrow_table = arrow_table.append_column("_phlo_ingested_at", ingested_at_col)
    arrow_table = arrow_table.append_column("_phlo_partition_date", partition_date_col)
    arrow_table = arrow_table.append_column("_phlo_run_id", run_id_col)

    pq.write_table(arrow_table, str(parquet_path))

    if context:
        context.log.debug(
            "Added _phlo_row_id, _phlo_ingested_at, _phlo_partition_date, _phlo_run_id columns"
        )
    logger.info(
        "dlt_metadata_injection_finished",
        parquet_path=str(parquet_path),
        row_count=num_rows,
    )

    return parquet_path


def validate_with_pandera(
    context,
    data: list[dict[str, Any]],
    schema_class: type[DataFrameModel],
    column_mapping: dict[str, str] | None = None,
    strict: bool = False,
) -> bool:
    """Validate extracted records against a Pandera schema.

    Args:
        context: Dagster context used for logging validation outcomes.
        data: Extracted records to validate.
        schema_class: Pandera ``DataFrameModel`` defining validation rules.
        column_mapping: Optional source-to-schema column rename mapping.
        strict: Whether to re-raise schema errors instead of returning ``False``.

    Returns:
        ``True`` when validation passes, ``False`` when it fails in non-strict mode.
    """

    try:
        logger.info(
            "dlt_pandera_validation_started",
            schema_name=schema_class.__name__,
            record_count=len(data),
            strict=strict,
            column_mapping_provided=column_mapping is not None,
        )
        context.log.info(f"Validating {len(data)} records with {schema_class.__name__}")

        df = pd.DataFrame(data)

        if column_mapping:
            df = df.rename(columns=column_mapping)

        schema = schema_class.to_schema()
        datetime_columns = [
            name
            for name, column in schema.columns.items()
            if isinstance(column.dtype, pandas_engine.DateTime)
        ]

        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        schema_class.validate(df, lazy=True)
        context.log.info("Pandera validation passed")
        logger.info(
            "dlt_pandera_validation_passed",
            schema_name=schema_class.__name__,
            record_count=len(data),
        )
        return True
    except pandera.errors.SchemaErrors as e:
        logger.warning(
            "dlt_pandera_validation_failed",
            schema_name=schema_class.__name__,
            record_count=len(data),
            strict=strict,
        )
        context.log.warning(f"Pandera validation failed: {e.failure_cases}")
        if strict:
            raise
        return False


def setup_dlt_pipeline(
    pipeline_name: str,
    dataset_name: str,
) -> tuple[Any, Path]:
    """Create a filesystem-backed DLT pipeline.

    Args:
        pipeline_name: DLT pipeline identifier.
        dataset_name: Target dataset name for staged output.

    Returns:
        Tuple of ``(pipeline, pipeline_working_directory)``.
    """

    pipelines_dir = Path("/tmp/phlo/dlt")
    pipelines_dir.mkdir(parents=True, exist_ok=True)
    bucket_url = str((pipelines_dir / "bucket").resolve())
    Path(bucket_url).mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.filesystem(bucket_url=bucket_url),
        dataset_name=dataset_name,
        pipelines_dir=str(pipelines_dir),
    )

    return pipeline, pipelines_dir / pipeline_name


def stage_to_parquet(
    context,
    pipeline: Any,
    dlt_source: Any,
    local_staging_root: Path,
) -> tuple[Path, float]:
    """Run DLT extraction and locate the staged parquet output.

    Args:
        context: Dagster context for logs.
        pipeline: Configured DLT pipeline object.
        dlt_source: DLT source/resource object to execute.
        local_staging_root: Root directory used to resolve relative parquet paths.

    Returns:
        Tuple of ``(parquet_path, elapsed_seconds)``.
    """

    start_time = time.time()
    logger.info(
        "dlt_stage_to_parquet_started",
        pipeline_name=getattr(pipeline, "pipeline_name", ""),
    )

    load_info: LoadInfo = pipeline.run(dlt_source, loader_file_format="parquet")
    if load_info is None:
        logger.error(
            "dlt_stage_to_parquet_missing_load_info",
            pipeline_name=getattr(pipeline, "pipeline_name", ""),
        )
        raise RuntimeError("DLT pipeline returned no load info")

    if not load_info.load_packages:
        logger.error(
            "dlt_stage_to_parquet_missing_load_packages",
            pipeline_name=getattr(pipeline, "pipeline_name", ""),
        )
        raise RuntimeError("DLT pipeline completed without load packages")

    completed_jobs = load_info.load_packages[0].jobs["completed_jobs"]
    parquet_files = [job for job in completed_jobs if job.file_path.endswith(".parquet")]
    if not parquet_files:
        logger.error(
            "dlt_stage_to_parquet_missing_parquet_output",
            pipeline_name=getattr(pipeline, "pipeline_name", ""),
            completed_job_count=len(completed_jobs),
        )
        raise RuntimeError("DLT pipeline completed without producing parquet files")

    parquet_path = Path(parquet_files[0].file_path)
    if not parquet_path.is_absolute():
        parquet_path = (local_staging_root / parquet_path).resolve()

    elapsed = time.time() - start_time
    context.log.info(f"DLT staging completed in {elapsed:.2f}s")
    context.log.debug(f"Parquet staged to {parquet_path}")
    logger.info(
        "dlt_stage_to_parquet_finished",
        pipeline_name=getattr(pipeline, "pipeline_name", ""),
        parquet_path=str(parquet_path),
        elapsed_seconds=round(elapsed, 3),
    )

    return parquet_path, elapsed


def merge_to_table_store(
    context,
    table_store: TableStore,
    table_config: TableConfig,
    parquet_path: Path,
    branch_name: str,
    merge_strategy: str = "merge",
    merge_config: dict[str, Any] | None = None,
) -> dict[str, int]:
    """Write staged parquet data into the configured table store via append or merge.

    Args:
        context: Dagster context used for progress logging.
        table_store: Table store capability used for table operations.
        table_config: Table configuration including schema, partitioning, and keys.
        parquet_path: Path to staged parquet data.
        branch_name: Nessie branch to write into.
        merge_strategy: Write strategy (``"append"`` or ``"merge"``).
        merge_config: Reserved merge configuration payload.

    Returns:
        Merge metrics emitted by the underlying Iceberg write operation.
    """

    merge_config = merge_config or {}
    table_name = table_config.full_table_name
    logger.info(
        "dlt_merge_to_table_store_started",
        table_name=table_name,
        branch_name=branch_name,
        merge_strategy=merge_strategy,
        merge_config_keys=sorted(merge_config.keys()),
    )

    context.log.info(f"Ensuring destination table {table_name} exists on branch {branch_name}...")
    table_store.ensure_table(
        table_name=table_name,
        schema=table_config.iceberg_schema,
        partition_spec=table_config.partition_spec,
        override_ref=branch_name,
    )

    def _coerce_parquet_to_table_schema(parquet_file: Path) -> Path:
        import tempfile

        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        from pyiceberg.types import (
            BooleanType,
            DateType,
            DoubleType,
            LongType,
            StringType,
            TimestamptzType,
        )

        arrow_table = pq.read_table(str(parquet_file))
        num_rows = len(arrow_table)

        def iceberg_type_to_arrow_type(iceberg_type: object) -> pa.DataType:
            """Map a subset of Iceberg primitive types to Arrow data types."""
            if isinstance(iceberg_type, StringType):
                return pa.string()
            if isinstance(iceberg_type, LongType):
                return pa.int64()
            if isinstance(iceberg_type, DoubleType):
                return pa.float64()
            if isinstance(iceberg_type, BooleanType):
                return pa.bool_()
            if isinstance(iceberg_type, TimestamptzType):
                return pa.timestamp("us", tz="UTC")
            if isinstance(iceberg_type, DateType):
                return pa.date32()
            return pa.string()

        desired_fields = list(table_config.iceberg_schema.fields)
        desired_names = [f.name for f in desired_fields]

        columns: list[pa.Array] = []
        for field in desired_fields:
            name = field.name
            target_type = iceberg_type_to_arrow_type(field.field_type)

            if name in arrow_table.column_names:
                col = arrow_table[name]
                try:
                    casted = pc.cast(col, target_type)
                except Exception:
                    logger.warning(
                        "dlt_merge_schema_cast_fallback",
                        table_name=table_name,
                        column_name=name,
                        target_type=str(target_type),
                    )
                    casted = pc.cast(pc.cast(col, pa.string()), target_type)
                columns.append(casted)
            else:
                columns.append(pa.nulls(num_rows, type=target_type))

        projected = pa.table(columns, names=desired_names)

        temp_dir = tempfile.mkdtemp()
        coerced_path = Path(temp_dir) / "coerced.parquet"
        pq.write_table(projected, str(coerced_path))
        return coerced_path

    parquet_path = _coerce_parquet_to_table_schema(parquet_path)

    if merge_strategy == "append":
        context.log.info(f"Appending data to destination table on branch {branch_name}...")
        merge_metrics = table_store.append_parquet(
            table_name=table_name,
            data_path=str(parquet_path),
            override_ref=branch_name,
        )
        context.log.info(f"Appended {merge_metrics['rows_inserted']} rows to {table_name}")
    elif merge_strategy == "merge":
        context.log.info(
            f"Merging data to destination table on branch {branch_name} (idempotent upsert)..."
        )
        merge_metrics = table_store.merge_parquet(
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
        logger.error(
            "dlt_merge_to_table_store_unknown_strategy",
            table_name=table_name,
            merge_strategy=merge_strategy,
        )
        raise ValueError(f"Unknown merge strategy: {merge_strategy}")

    logger.info(
        "dlt_merge_to_table_store_finished",
        table_name=table_name,
        merge_strategy=merge_strategy,
        rows_inserted=merge_metrics.get("rows_inserted"),
        rows_deleted=merge_metrics.get("rows_deleted"),
    )
    return merge_metrics
