from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal

from pandera.pandas import DataFrameModel
from phlo.capabilities import (
    AssetCheckSpec,
    AssetSpec,
    MaterializeResult,
    PartitionSpec,
    RunResult,
    RunSpec,
    register_asset,
)
from phlo.capabilities.runtime import RuntimeContext
from phlo.exceptions import PhloConfigError
from phlo_quality.pandera_asset_checks import (
    PANDERA_CONTRACT_CHECK_NAME,
    PanderaContractEvaluation,
    evaluate_pandera_contract_parquet,
    pandera_contract_asset_check_result,
)

from phlo_dlt.converter import pandera_to_iceberg
from phlo_dlt.dlt_helpers import get_branch_from_context
from phlo_dlt.registry import TableConfig

_INGESTION_ASSETS: list[AssetSpec] = []


def get_ingestion_assets() -> list[AssetSpec]:
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


def _resolve_iceberg_resource(context: RuntimeContext) -> Any:
    iceberg = None
    resources = context.resources
    if isinstance(resources, dict):
        iceberg = resources.get("iceberg")
    elif resources is not None:
        iceberg = getattr(resources, "iceberg", None)
    if iceberg is None:
        try:
            iceberg = context.get_resource("iceberg")
        except Exception:
            iceberg = None
    if iceberg is None:
        raise PhloConfigError(
            message="Iceberg resource not available in runtime context",
            suggestions=["Install phlo-iceberg or configure an Iceberg resource provider."],
        )
    return iceberg


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
        check_specs: list[AssetCheckSpec] = []
        if validate and table_config.validation_schema is not None:
            check_specs = [
                AssetCheckSpec(
                    name=PANDERA_CONTRACT_CHECK_NAME,
                    asset_key=f"dlt_{table_config.table_name}",
                    blocking=bool(strict_validation),
                    description=f"Pandera schema contract for {table_config.table_name}",
                )
            ]

        def run(runtime: RuntimeContext) -> Iterator[RunResult]:
            partition_date = runtime.partition_key
            if not partition_date:
                raise PhloConfigError(
                    message="Missing partition key for ingestion asset",
                    suggestions=["Run the asset with a partition key (YYYY-MM-DD)."],
                )

            branch_name = get_branch_from_context(runtime)
            run_id = runtime.run_id or "unknown"
            logger = runtime.logger

            logger.info(f"Starting ingestion for partition {partition_date}")
            logger.info(f"Ingesting to branch: {branch_name}")
            logger.info(f"Target table: {table_config.full_table_name}")

            logger.info("Calling user function to get DLT source...")
            try:
                from phlo_dlt.executor import DltIngester

                iceberg = _resolve_iceberg_resource(runtime)

                ingester = DltIngester(
                    context=runtime,
                    logger=logger,
                    table_config=table_config,
                    iceberg_resource=iceberg,
                    dlt_source_func=func,
                    add_metadata_columns=add_metadata_columns,
                    merge_strategy=merge_strategy,
                    merge_config=merge_cfg,
                )

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
                            asset_key=f"dlt_{table_config.table_name}",
                            schema_class=table_config.validation_schema,
                            query_or_sql="status:no_data",
                        )
                        yield check_result
                    yield MaterializeResult(
                        metadata={
                            "branch": branch_name,
                            "partition_date": partition_date,
                            "rows_loaded": 0,
                            "status": "no_data",
                        },
                        status="no_data",
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
                        logger.error(f"Pandera contract evaluation failed: {exc}")
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
                        asset_key=f"dlt_{table_config.table_name}",
                        schema_class=table_config.validation_schema,
                        query_or_sql=query_or_sql,
                    )
                    yield check_result
                    if strict_validation and not evaluation.passed:
                        raise RuntimeError("Pandera contract validation failed")

                yield MaterializeResult(
                    metadata={
                        "branch": branch_name,
                        "partition_date": partition_date,
                        "rows_inserted": result.rows_inserted,
                        "rows_deleted": result.rows_deleted,
                        "unique_key": table_config.unique_key,
                        "table_name": table_config.full_table_name,
                        "dlt_elapsed_seconds": result.metadata.get("dlt_elapsed_seconds", 0.0),
                        "total_elapsed_seconds": result.metadata.get("total_elapsed_seconds", 0.0),
                    },
                    status=result.status,
                )

            except Exception:
                raise

        asset_spec = AssetSpec(
            key=f"dlt_{table_config.table_name}",
            group=group,
            description=func.__doc__ or f"Ingests {table_config.table_name} data to Iceberg",
            kinds={"dlt", "iceberg"},
            tags={"source": "dlt"},
            metadata={
                "table_name": table_config.table_name,
                "unique_key": table_config.unique_key,
                "group": table_config.group_name,
            },
            partitions=PartitionSpec(kind="daily"),
            resources={"iceberg"},
            run=RunSpec(
                fn=run,
                max_runtime_seconds=max_runtime_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                cron=cron,
                freshness_hours=freshness_hours,
            ),
            checks=check_specs,
        )

        _INGESTION_ASSETS.append(asset_spec)
        register_asset(asset_spec)
        setattr(func, "_phlo_table_config", table_config)
        return func

    return decorator
