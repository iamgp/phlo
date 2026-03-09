"""Decorator for registering Sling replication assets."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Literal

from phlo.capabilities import AssetSpec, MaterializeResult, PartitionSpec, RunSpec
from phlo.contracts import Consumer, SLA, normalize_consumers, serialize_consumers, serialize_sla
from phlo.capabilities.runtime import RuntimeContext
from phlo.exceptions import PhloConfigError
from phlo.logging import log_event

from phlo_sling.registry import ReplicationConfig
from phlo_sling.settings import get_settings

_SLING_ASSETS: list[AssetSpec] = []


def get_sling_assets() -> list[AssetSpec]:
    """Return registered Sling replication asset specifications.

    Returns:
        A shallow copy of all assets created via `phlo_sling_replication`.
    """
    return list(_SLING_ASSETS)


def clear_sling_assets() -> None:
    """Clear all registered Sling replication asset specifications."""
    _SLING_ASSETS.clear()


def _validate_replication_mode(mode: str) -> None:
    """Validate the replication mode is supported.

    Args:
        mode: Replication mode string.

    Raises:
        PhloConfigError: If mode is not one of the supported values.
    """
    valid_modes = {"full-refresh", "incremental", "snapshot", "backfill"}
    if mode not in valid_modes:
        raise PhloConfigError(
            message=f"Invalid replication mode: {mode}",
            suggestions=[f"Use one of: {', '.join(sorted(valid_modes))}"],
        )


def _validate_incremental_config(mode: str, update_key: str | None) -> None:
    """Validate incremental mode has a required update_key.

    Args:
        mode: Replication mode string.
        update_key: Column used as cursor for incremental replication.

    Raises:
        PhloConfigError: If mode is incremental but update_key is missing.
    """
    if mode == "incremental" and not update_key:
        raise PhloConfigError(
            message="Incremental mode requires an update_key",
            suggestions=["Set update_key to a timestamp or incrementing column"],
        )


def phlo_sling_replication(
    stream_name: str,
    table_name: str,
    source_conn: str,
    group: str,
    *,
    target_conn: str | None = None,
    mode: Literal["full-refresh", "incremental", "snapshot", "backfill"] | None = None,
    primary_key: list[str] | str | None = None,
    update_key: str | None = None,
    object: str | None = None,
    select: list[str] | None = None,
    where: str | None = None,
    source_options: dict[str, Any] | None = None,
    target_options: dict[str, Any] | None = None,
    cron: str | None = None,
    freshness_hours: tuple[int, int] | None = None,
    max_runtime_seconds: int = 600,
    max_retries: int = 3,
    retry_delay_seconds: int = 30,
    owner: str | None = None,
    consumers: list[Consumer | str] | None = None,
    sla: SLA | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function as a Sling-backed replication asset.

    The decorated function receives a `RuntimeContext` and returns either
    `None` (use decorator parameters) or a `dict` of Sling overrides
    (e.g., dynamic `where` clause based on partition date).

    Args:
        stream_name: Source stream identifier (e.g., 'public.users' or 'my_schema.*').
        table_name: Target table name in the table store (without namespace prefix).
        source_conn: Sling source connection name.
        group: Dagster/asset group name.
        target_conn: Sling target connection name. If set and object is omitted,
            Phlo targets `<namespace>.<table_name>`.
        mode: Replication mode. None uses `SLING_DEFAULT_MODE`.
        primary_key: Column(s) used as primary key. String or list of strings.
        update_key: Column used as cursor for incremental replication.
        object: Target object path for file-based targets.
        select: Column selection list. None means all columns.
        where: SQL WHERE clause for source filtering.
        source_options: Additional Sling source options dict.
        target_options: Additional Sling target options dict.
        cron: Optional cron schedule for automated runs.
        freshness_hours: Optional freshness policy window.
        max_runtime_seconds: Max runtime before timeout.
        max_retries: Max retry attempts for failed runs.
        retry_delay_seconds: Delay between retries in seconds.
        owner: Optional asset owner/team identifier.
        consumers: Optional downstream consumer metadata.
        sla: Optional SLA metadata for freshness/quality alerting.

    Returns:
        A decorator that registers replication metadata and returns the original function.

    Raises:
        PhloConfigError: If mode or configuration is invalid.
    """
    resolved_mode = mode or get_settings().sling_default_mode
    _validate_replication_mode(resolved_mode)
    _validate_incremental_config(resolved_mode, update_key)

    pk_list = [primary_key] if isinstance(primary_key, str) else (primary_key or [])

    repl_config = ReplicationConfig(
        stream_name=stream_name,
        table_name=table_name,
        source_conn=source_conn,
        target_conn=target_conn,
        mode=resolved_mode,
        primary_key=pk_list,
        update_key=update_key,
        group_name=group,
        object=object,
        select=select or [],
        where=where,
        source_options=source_options or {},
        target_options=target_options or {},
    )
    normalized_consumers = normalize_consumers(consumers)

    def decorator(func: Callable[..., Any]) -> Any:
        """Wrap a replication source function as a Phlo asset definition."""

        def run(runtime: RuntimeContext) -> Iterator[MaterializeResult]:
            """Execute the Sling replication and yield results.

            Args:
                runtime: Orchestrator runtime context with resources and metadata.

            Yields:
                MaterializeResult with replication metadata.
            """
            partition_date = runtime.partition_key or "latest"
            run_id = runtime.run_id or "unknown"
            logger = runtime.logger

            log_event(logger, "info", "starting_sling_replication", partition_date=partition_date)
            log_event(
                logger,
                "info",
                "sling_stream_selected",
                stream_name=repl_config.stream_name,
                table_name=repl_config.full_table_name,
                mode=repl_config.mode,
            )

            try:
                from phlo_sling.executor import SlingIngester

                overrides = func(runtime)

                ingester = SlingIngester(
                    context=runtime,
                    logger=logger,
                    replication_config=repl_config,
                    source_func=func,
                    overrides=overrides if isinstance(overrides, dict) else None,
                )

                result = ingester.run_ingestion(
                    partition_key=partition_date,
                    parameters={
                        "run_id": run_id,
                    },
                )

                if result.status == "no_data":
                    yield MaterializeResult(
                        metadata={
                            "partition_date": partition_date,
                            "rows_loaded": 0,
                            "status": "no_data",
                            "stream_name": repl_config.stream_name,
                        },
                        status="no_data",
                    )
                    return

                yield MaterializeResult(
                    metadata={
                        "partition_date": partition_date,
                        "rows_inserted": result.rows_inserted,
                        "rows_deleted": result.rows_deleted,
                        "table_name": repl_config.full_table_name,
                        "stream_name": repl_config.stream_name,
                        "mode": repl_config.mode,
                        "sling_elapsed_seconds": result.metadata.get("sling_elapsed_seconds", 0.0),
                        "total_elapsed_seconds": result.metadata.get("total_elapsed_seconds", 0.0),
                    },
                    status=result.status,
                )

            except Exception:
                raise

        asset_spec = AssetSpec(
            key=repl_config.asset_key,
            group=group,
            description=(
                func.__doc__
                or f"Replicates {repl_config.stream_name} to {repl_config.full_table_name}"
            ),
            kinds={"sling", "replication"},
            tags={"source": "sling", "mode": repl_config.mode},
            metadata={
                "stream_name": repl_config.stream_name,
                "table_name": repl_config.table_name,
                "source_conn": repl_config.source_conn,
                "mode": repl_config.mode,
                "primary_key": repl_config.primary_key,
                "update_key": repl_config.update_key,
                "group": repl_config.group_name,
                "owner": owner,
                "consumers": serialize_consumers(normalized_consumers),
                "sla": serialize_sla(sla),
            },
            partitions=PartitionSpec(kind="daily"),
            resources=set(),
            run=RunSpec(
                fn=run,
                max_runtime_seconds=max_runtime_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                cron=cron,
                freshness_hours=freshness_hours,
            ),
            checks=[],
        )

        _SLING_ASSETS.append(asset_spec)
        setattr(func, "_phlo_replication_config", repl_config)
        return func

    return decorator
