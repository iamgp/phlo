from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal

import dagster as dg
from pandera.pandas import DataFrameModel
from phlo_dagster.partitions import daily_partition
from phlo.exceptions import PhloConfigError
from phlo_quality.pandera_asset_checks import (
    PANDERA_CONTRACT_CHECK_NAME,
    PanderaContractEvaluation,
    evaluate_pandera_contract_parquet,
    pandera_contract_asset_check_result,
)
from phlo_iceberg.resource import IcebergResource

from phlo_dlt.converter import pandera_to_iceberg
from phlo_dlt.dlt_helpers import (
    get_branch_from_context,
)
from phlo_dlt.registry import TableConfig

_INGESTION_ASSETS: list[Any] = []


def get_ingestion_assets() -> list[Any]:
    return list(_INGESTION_ASSETS)


def clear_ingestion_assets() -> None:
    _INGESTION_ASSETS.clear()


def _validate_unique_key_in_schema(unique_key: str, schema: type[Any] | None) -> None:
    if schema is None:
        return
    annotations = getattr(schema, "__annotations__", {})
    if unique_key not in annotations:
        raise PhloConfigError(
            message=f"unique_key '{unique_key}' not found in schema {schema.__name__}",
            suggestions=[
                f"Add `{unique_key}` to {schema.__name__} schema annotations",
                "Or update unique_key to match an existing schema field",
            ],
        )


def _validate_merge_config(
    merge_strategy: str,
    unique_key: str,
    merge_config: dict[str, Any] | None,
) -> None:
    if merge_strategy not in ("append", "merge"):
        raise PhloConfigError(
            message=f"Invalid merge_strategy: {merge_strategy}",
            suggestions=["Use merge_strategy='append' or merge_strategy='merge'"],
        )

    if merge_config is None:
        return

    if not isinstance(merge_config, dict):
        raise PhloConfigError(
            message="merge_config must be a dict",
            suggestions=["Pass merge_config={'deduplication': True, ...}"],
        )

    if merge_config.get("deduplication") and not unique_key:
        raise PhloConfigError(
            message="deduplication requires a unique_key",
            suggestions=["Set unique_key parameter to a valid column name"],
        )


def _default_merge_config(
    merge_strategy: str,
    merge_config: dict[str, Any] | None,
) -> dict[str, Any]:
    config = merge_config.copy() if merge_config else {}

    if merge_strategy == "append":
        config.setdefault("deduplication", False)
    elif merge_strategy == "merge":
        config.setdefault("deduplication", True)
        config.setdefault("deduplication_method", "last")

    return config


def phlo_ingestion(
    table_name: str,
    unique_key: str,
    group: str,
    validation_schema: type[Any] | None = None,
    iceberg_schema: Any | None = None,
    partition_spec: Any | None = None,
    cron: str | None = None,
    freshness_hours: tuple[int, int] | None = None,
    max_runtime_seconds: int = 300,
    max_retries: int = 3,
    retry_delay_seconds: int = 30,
    validate: bool = True,
    strict_validation: bool = True,
    merge_strategy: Literal["append", "merge"] = "merge",
    merge_config: dict[str, Any] | None = None,
    add_metadata_columns: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    _validate_unique_key_in_schema(unique_key, validation_schema)
    _validate_merge_config(merge_strategy, unique_key, merge_config)

    merge_cfg = _default_merge_config(merge_strategy, merge_config)

    if iceberg_schema is None and validation_schema is not None:
        iceberg_schema = pandera_to_iceberg(validation_schema)
    elif iceberg_schema is None:
        raise PhloConfigError(
            message="Missing required schema parameter",
            suggestions=[
                "Add validation_schema parameter (recommended): validation_schema=MyPanderaSchema",
                "Or add iceberg_schema parameter (manual): iceberg_schema=IcebergSchema(...)",
            ],
        )

    from typing import cast

    table_config = TableConfig(
        table_name=table_name,
        iceberg_schema=iceberg_schema,
        validation_schema=cast("type[DataFrameModel] | None", validation_schema),
        unique_key=unique_key,
        group_name=group,
        partition_spec=partition_spec,
    )

    def decorator(func: Callable[..., Any]) -> Any:
        check_specs = None
        if validate and table_config.validation_schema is not None:
            check_specs = [
                dg.AssetCheckSpec(
                    name=PANDERA_CONTRACT_CHECK_NAME,
                    asset=f"dlt_{table_config.table_name}",
                    blocking=bool(strict_validation),
                    description=f"Pandera schema contract for {table_config.table_name}",
                )
            ]

        @dg.asset(
            name=f"dlt_{table_config.table_name}",
            group_name=group,
            partitions_def=daily_partition,
            description=func.__doc__ or f"Ingests {table_config.table_name} data to Iceberg",
            kinds={"dlt", "iceberg"},
            check_specs=check_specs,
            op_tags={"dagster/max_runtime": max_runtime_seconds},
            retry_policy=dg.RetryPolicy(max_retries=max_retries, delay=retry_delay_seconds),
            automation_condition=(dg.AutomationCondition.on_cron(cron) if cron else None),
            freshness_policy=(
                dg.FreshnessPolicy.time_window(
                    warn_window=timedelta(hours=freshness_hours[0]),
                    fail_window=timedelta(hours=freshness_hours[1]),
                )
                if freshness_hours
                else None
            ),
        )
        def wrapper(
            context, iceberg: IcebergResource
        ) -> Iterator[dg.AssetCheckResult | dg.MaterializeResult]:
            partition_date = context.partition_key
            f"{table_config.table_name}_{partition_date.replace('-', '_')}"
            branch_name = get_branch_from_context(context)
            run_id = context.run.run_id if hasattr(context, "run") else None
            context.log.info(f"Starting ingestion for partition {partition_date}")
            context.log.info(f"Ingesting to branch: {branch_name}")
            context.log.info(f"Target table: {table_config.full_table_name}")

            context.log.info("Calling user function to get DLT source...")
            try:
                # 1. Initialize Ingester (Orchestrator Independent)
                from phlo_dlt.executor import DltIngester

                # Wrap Dagster context's logger
                # DltIngester expects an object with .info(), .warning() etc
                # context.log in Dagster satisfies this.

                ingester = DltIngester(
                    context=context,
                    logger=context.log,
                    table_config=table_config,
                    iceberg_resource=iceberg,
                    dlt_source_func=func,
                    add_metadata_columns=add_metadata_columns,
                    merge_strategy=merge_strategy,
                    merge_config=merge_cfg,
                )

                # 2. Run Ingestion
                # DltIngester handles source execution, pipeline setup, parquet staging, and iceberg merge
                result = ingester.run_ingestion(
                    partition_key=partition_date,
                    parameters={"branch_name": branch_name, "run_id": run_id},
                )

                if result.status == "no_data":
                    if validate and table_config.validation_schema is not None:
                        evaluation = PanderaContractEvaluation(
                            passed=True,
                            failed_count=0,
                            total_count=0,
                            sample=[],
                            error=None,
                        )
                        check_result = pandera_contract_asset_check_result(
                            evaluation,
                            partition_key=partition_date,
                            schema_class=table_config.validation_schema,
                            query_or_sql="status:no_data",
                        )
                        yield check_result
                    yield dg.MaterializeResult(
                        metadata={
                            "branch": branch_name,
                            "partition_date": dg.MetadataValue.text(partition_date),
                            "rows_loaded": dg.MetadataValue.int(0),
                            "status": dg.MetadataValue.text("no_data"),
                        }
                    )
                    return

                if validate and table_config.validation_schema is not None:
                    parquet_path = result.metadata.get("parquet_path")
                    query_or_sql = (
                        f"parquet://{parquet_path}" if parquet_path else "parquet://<missing>"
                    )
                    try:
                        if parquet_path is None:
                            raise FileNotFoundError("Missing parquet_path in ingestion metadata")
                        evaluation = evaluate_pandera_contract_parquet(
                            Path(parquet_path),
                            schema_class=table_config.validation_schema,
                        )
                    except Exception as exc:
                        context.log.error(f"Pandera contract evaluation failed: {exc}")
                        evaluation = PanderaContractEvaluation(
                            passed=False,
                            failed_count=1,
                            total_count=0,
                            sample=[{"error": str(exc)}],
                            error=str(exc),
                        )
                    check_result = pandera_contract_asset_check_result(
                        evaluation,
                        partition_key=partition_date,
                        schema_class=table_config.validation_schema,
                        query_or_sql=query_or_sql,
                    )
                    yield check_result
                    if strict_validation and not evaluation.passed:
                        raise dg.Failure("Pandera contract validation failed")

                # 3. Yield Results
                # Ingester handles emission of Phlo events internally.
                # We simply translate the IngestionResult to Dagster MaterializeResult

                yield dg.MaterializeResult(
                    metadata={
                        "branch": branch_name,
                        "partition_date": dg.MetadataValue.text(partition_date),
                        "rows_inserted": dg.MetadataValue.int(result.rows_inserted),
                        "rows_deleted": dg.MetadataValue.int(result.rows_deleted),
                        "unique_key": dg.MetadataValue.text(table_config.unique_key),
                        "table_name": dg.MetadataValue.text(table_config.full_table_name),
                        "dlt_elapsed_seconds": dg.MetadataValue.float(
                            result.metadata.get("dlt_elapsed_seconds", 0.0)
                        ),
                        "total_elapsed_seconds": dg.MetadataValue.float(
                            result.metadata.get("total_elapsed_seconds", 0.0)
                        ),
                    }
                )

            except Exception:
                # Ingester emits failure events before raising
                raise

        _INGESTION_ASSETS.append(wrapper)
        return wrapper

    return decorator
