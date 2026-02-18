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
    """Return registered ingestion asset specifications.

    Returns:
        A shallow copy of all ingestion assets created via `phlo_ingestion`.
    """
    return list(_INGESTION_ASSETS)


def clear_ingestion_assets() -> None:
    """Clear all registered ingestion asset specifications."""
    _INGESTION_ASSETS.clear()


def _validate_unique_key_in_schema(unique_key: str, schema: type[Any] | None) -> None:
    """Validate that the configured unique key exists in the schema annotations.

    Args:
        unique_key: Column name used to identify unique records.
        schema: Optional schema class used for validation.

    Raises:
        PhloConfigError: If `schema` is provided and `unique_key` is missing.
    """
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
    """Validate merge strategy and merge configuration semantics.

    Args:
        merge_strategy: Write strategy for ingestion (`append` or `merge`).
        unique_key: Column name used for deduplication and merge operations.
        merge_config: Optional merge behavior overrides.

    Raises:
        PhloConfigError: If strategy or config values are invalid.
    """
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
    """Build merge configuration defaults for the selected strategy.

    Args:
        merge_strategy: Write strategy for ingestion (`append` or `merge`).
        merge_config: Optional user-provided merge configuration.

    Returns:
        Effective merge configuration with strategy defaults applied.
    """
    config = merge_config.copy() if merge_config else {}

    if merge_strategy == "append":
        config.setdefault("deduplication", False)
    elif merge_strategy == "merge":
        config.setdefault("deduplication", True)
        config.setdefault("deduplication_method", "last")

    return config


def _resolve_table_store_resource(context: RuntimeContext) -> Any:
    """Resolve the table-store resource from runtime resources.

    Args:
        context: Runtime context passed to the ingestion run function.

    Returns:
        The resolved table-store resource object.

    Raises:
        PhloConfigError: If no table-store resource can be resolved.
    """
    table_store = None
    resources = context.resources
    if isinstance(resources, dict):
        table_store = resources.get("table_store") or resources.get("iceberg")
    elif resources is not None:
        table_store = getattr(resources, "table_store", None) or getattr(resources, "iceberg", None)
    if table_store is None:
        try:
            table_store = context.get_resource("table_store")
        except Exception:
            table_store = None
    if table_store is None:
        try:
            table_store = context.get_resource("iceberg")
        except Exception:
            table_store = None
    if table_store is None:
        raise PhloConfigError(
            message="Table store resource not available in runtime context",
            suggestions=[
                "Configure a `table_store` resource provider (or legacy `iceberg` resource)."
            ],
        )
    return table_store


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
    """Register a function as a DLT-backed ingestion asset.

    Args:
        table_name: Destination Iceberg table name (without `dlt_` prefix).
        unique_key: Column used for deduplication and merge operations.
        group: Dagster/asset group name.
        validation_schema: Optional Pandera schema for data contract checks.
        iceberg_schema: Optional explicit Iceberg schema.
        partition_spec: Optional partition specification override.
        cron: Optional cron schedule for automated runs.
        freshness_hours: Optional freshness policy window.
        max_runtime_seconds: Max runtime before the run is considered timed out.
        max_retries: Max retry attempts for failed runs.
        retry_delay_seconds: Delay between retries in seconds.
        validate: Whether to execute Pandera contract checks.
        strict_validation: Whether failed validation should fail the run.
        merge_strategy: Ingestion strategy (`append` or `merge`).
        merge_config: Optional merge behavior overrides.
        add_metadata_columns: Whether ingestion metadata columns should be added.

    Returns:
        A decorator that registers ingestion metadata and returns the original function.

    Raises:
        PhloConfigError: If schema/merge configuration is invalid.
    """
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
        """Wrap an ingestion source function as a Phlo asset definition."""
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
            """Execute one partitioned ingestion run for the wrapped source function."""
            partition_date = runtime.partition_key
            if not partition_date:
                raise PhloConfigError(
                    message="Missing partition key for ingestion asset",
                    suggestions=["Run the asset with a partition key (YYYY-MM-DD)."],
                )

            branch_name = get_branch_from_context(runtime)
            run_id = runtime.run_id or "unknown"
            logger = runtime.logger

            logger.info("starting_ingestion", partition_date=partition_date)
            logger.info("ingesting_to_branch", branch_name=branch_name)
            logger.info("target_table_selected", table_name=table_config.full_table_name)

            logger.info("Calling user function to get DLT source...")
            try:
                from phlo_dlt.executor import DltIngester

                table_store = _resolve_table_store_resource(runtime)

                ingester = DltIngester(
                    context=runtime,
                    logger=logger,
                    table_config=table_config,
                    table_store_resource=table_store,
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
                    logger.info(
                        "pandera_contract_evaluation_started",
                        table_name=table_config.full_table_name,
                        partition_date=partition_date,
                        parquet_path=str(parquet_path) if parquet_path is not None else None,
                    )
                    try:
                        if parquet_path is None:
                            raise FileNotFoundError("Missing parquet_path in ingestion metadata")
                        evaluation = evaluate_pandera_contract_parquet(
                            Path(parquet_path),
                            schema_class=table_config.validation_schema,
                        )
                        if evaluation.passed:
                            logger.info(
                                "pandera_contract_evaluation_passed",
                                table_name=table_config.full_table_name,
                                partition_date=partition_date,
                                parquet_path=str(parquet_path),
                                total_count=evaluation.total_count,
                                failed_count=evaluation.failed_count,
                            )
                        else:
                            logger.warning(
                                "pandera_contract_evaluation_failed",
                                table_name=table_config.full_table_name,
                                partition_date=partition_date,
                                parquet_path=str(parquet_path),
                                total_count=evaluation.total_count,
                                failed_count=evaluation.failed_count,
                                error=evaluation.error,
                            )
                    except Exception as exc:
                        logger.error(
                            "pandera_contract_evaluation_failed",
                            table_name=table_config.full_table_name,
                            partition_date=partition_date,
                            parquet_path=str(parquet_path) if parquet_path is not None else None,
                            error=str(exc),
                            exc_info=True,
                        )
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
        setattr(func, "_phlo_table_config", table_config)
        return func

    return decorator
