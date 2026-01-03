from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dlt
import pandas as pd
import pandera.errors
from dlt.common.pipeline import LoadInfo
from pandera.engines import pandas_engine
from pandera.pandas import DataFrameModel
from phlo_lineage import generate_row_id
from phlo_iceberg.resource import IcebergResource

from phlo_dlt.registry import TableConfig


def get_branch_from_context(context) -> str:
    tags = getattr(context, "tags", None) or {}
    branch = tags.get("branch")
    if isinstance(branch, str) and branch:
        return branch

    run = getattr(context, "run", None)
    if run is not None:
        run_tags = getattr(run, "tags", {}) or {}
        branch = run_tags.get("branch")
        if isinstance(branch, str) and branch:
            return branch

    run_config = getattr(context, "run_config", {}) or {}
    if isinstance(run_config, dict) and "branch_name" in run_config:
        branch = run_config.get("branch_name")
        if isinstance(branch, str) and branch:
            return branch

    return "main"


def inject_metadata_columns(
    parquet_path: Path,
    partition_date: str,
    run_id: str,
    context: Any = None,
) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    arrow_table = pq.read_table(str(parquet_path))
    num_rows = len(arrow_table)

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

    return parquet_path


def validate_with_pandera(
    context,
    data: list[dict[str, Any]],
    schema_class: type[DataFrameModel],
    column_mapping: dict[str, str] | None = None,
    strict: bool = False,
) -> bool:
    try:
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
        return True
    except pandera.errors.SchemaErrors as e:
        context.log.warning(f"Pandera validation failed: {e.failure_cases}")
        if strict:
            raise
        return False


def setup_dlt_pipeline(
    pipeline_name: str,
    dataset_name: str,
) -> tuple[Any, Path]:
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
    start_time = time.time()

    load_info: LoadInfo = pipeline.run(dlt_source, loader_file_format="parquet")
    if load_info is None:
        raise RuntimeError("DLT pipeline returned no load info")

    completed_jobs = load_info.load_packages[0].jobs["completed_jobs"]
    parquet_files = [job for job in completed_jobs if job.file_path.endswith(".parquet")]
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
    merge_config = merge_config or {}
    table_name = table_config.full_table_name

    context.log.info(f"Ensuring Iceberg table {table_name} exists on branch {branch_name}...")
    iceberg.ensure_table(
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
        context.log.info(f"Appending data to Iceberg table on branch {branch_name}...")
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
