"""
Iceberg table maintenance jobs and schedules for Dagster.

Provides scheduled maintenance operations including snapshot expiration,
orphan file cleanup, and table statistics collection for Iceberg tables.
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, Any

import dagster as dg
from phlo.hooks import TelemetryEventContext, TelemetryEventEmitter
from pydantic import Field

from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.tables import expire_snapshots, get_table_stats, remove_orphan_files

logger = logging.getLogger(__name__)


class MaintenanceConfig(dg.Config):
    """Configuration for table maintenance operations."""

    # Namespace to run maintenance on (or 'all' for all namespaces)
    namespace: str = "raw"
    # Expire snapshots older than this many days (must be positive)
    snapshot_retention_days: Annotated[int, Field(gt=0)] = 7
    # Always retain at least this many snapshots (must be non-negative)
    snapshot_retain_last: Annotated[int, Field(ge=0)] = 5
    # Only remove orphan files older than this many days (must be positive)
    orphan_retention_days: Annotated[int, Field(gt=0)] = 3
    # If True, only list orphan files without deleting
    orphan_dry_run: bool = True
    # Nessie branch reference
    ref: str = "main"


def _maintenance_tags(
    config: MaintenanceConfig,
    *,
    operation: str,
    dry_run: bool | None = None,
    status: str | None = None,
) -> dict[str, str]:
    tags = {
        "maintenance": "true",
        "operation": operation,
        "namespace": config.namespace,
        "ref": config.ref,
    }
    if dry_run is not None:
        tags["dry_run"] = str(dry_run).lower()
    if status:
        tags["status"] = status
    return tags


def _maintenance_payload(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
    *,
    operation: str,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "operation": operation,
        "namespace": config.namespace,
        "ref": config.ref,
        "run_id": context.run_id,
        "job_name": context.job_name,
    }
    payload.update(extra)
    return payload


def _maintenance_log_extra(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
    *,
    operation: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "maintenance_op": operation,
        "namespace": config.namespace,
        "ref": config.ref,
        "run_id": context.run_id,
        "job_name": context.job_name,
        **extra,
    }


def _emit_maintenance_metrics(
    emitter: TelemetryEventEmitter,
    *,
    duration_seconds: float,
    tables_processed: int,
    errors: int,
    snapshots_deleted: int | None = None,
    orphan_files: int | None = None,
    total_records: int | None = None,
    total_size_mb: float | None = None,
) -> None:
    emitter.emit_metric(name="iceberg.maintenance.run", value=1, unit="run")
    emitter.emit_metric(
        name="iceberg.maintenance.duration_seconds",
        value=duration_seconds,
        unit="seconds",
    )
    emitter.emit_metric(
        name="iceberg.maintenance.tables_processed",
        value=tables_processed,
        unit="tables",
    )
    emitter.emit_metric(name="iceberg.maintenance.errors", value=errors, unit="errors")
    if snapshots_deleted is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.snapshots_deleted",
            value=snapshots_deleted,
            unit="snapshots",
        )
    if orphan_files is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.orphan_files",
            value=orphan_files,
            unit="files",
        )
    if total_records is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.total_records",
            value=total_records,
            unit="records",
        )
    if total_size_mb is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.total_size_mb",
            value=total_size_mb,
            unit="mb",
        )


def _list_tables(namespace: str, ref: str) -> list[str]:
    """List all tables in a namespace."""
    from pyiceberg.exceptions import NoSuchNamespaceError

    catalog = get_catalog(ref=ref)
    try:
        tables = catalog.list_tables(namespace)
        return [f"{namespace}.{table[1]}" for table in tables]
    except NoSuchNamespaceError:
        logger.info(f"Namespace {namespace} does not exist, skipping")
        return []
    except Exception:
        logger.exception(f"Failed to list tables in namespace {namespace}")
        return []


def _list_namespaces(ref: str) -> list[str]:
    """List all namespaces."""
    catalog = get_catalog(ref=ref)
    try:
        namespaces = catalog.list_namespaces()
        return [ns[0] for ns in namespaces]
    except Exception:
        logger.exception("Failed to list namespaces")
        return []


@dg.op
def expire_table_snapshots(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
) -> dict[str, Any]:
    """Expire old snapshots from all tables in the specified namespace."""
    results = {"tables_processed": 0, "total_snapshots_deleted": 0, "errors": []}
    operation = "expire_snapshots"
    start_time = time.time()
    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(tags=_maintenance_tags(config, operation=operation))
    )
    context.log.info(
        "Starting Iceberg maintenance operation",
        extra=_maintenance_log_extra(context, config, operation=operation, phase="start"),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.start",
        level="info",
        payload=_maintenance_payload(context, config, operation=operation),
    )

    if config.namespace == "all":
        namespaces = _list_namespaces(config.ref)
    else:
        namespaces = [config.namespace]

    for namespace in namespaces:
        tables = _list_tables(namespace, config.ref)
        for table_name in tables:
            try:
                result = expire_snapshots(
                    table_name=table_name,
                    older_than_days=config.snapshot_retention_days,
                    retain_last=config.snapshot_retain_last,
                    ref=config.ref,
                )
                results["tables_processed"] += 1
                results["total_snapshots_deleted"] += result["deleted_snapshots"]
                context.log.info(
                    f"Expired {result['deleted_snapshots']} snapshots from {table_name}",
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        snapshots_deleted=result["deleted_snapshots"],
                    ),
                )
            except Exception as e:
                error_msg = f"Failed to expire snapshots for {table_name}: {e}"
                context.log.warning(
                    error_msg,
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        error=str(e),
                    ),
                )
                results["errors"].append(error_msg)

    duration_seconds = time.time() - start_time
    status = "success" if not results["errors"] else "failure"
    summary_payload = _maintenance_payload(
        context,
        config,
        operation=operation,
        status=status,
        duration_seconds=duration_seconds,
        tables_processed=results["tables_processed"],
        snapshots_deleted=results["total_snapshots_deleted"],
        errors=len(results["errors"]),
    )
    context.log.info(
        "Completed Iceberg maintenance operation",
        extra=_maintenance_log_extra(
            context,
            config,
            operation=operation,
            status=status,
            duration_seconds=duration_seconds,
            tables_processed=results["tables_processed"],
            snapshots_deleted=results["total_snapshots_deleted"],
            errors=len(results["errors"]),
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.complete",
        level="info",
        payload=summary_payload,
    )
    if results["errors"]:
        telemetry.emit_log(
            name="iceberg.maintenance.failed",
            level="error",
            payload=summary_payload,
        )
    metrics_emitter = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=_maintenance_tags(config, operation=operation, status=status)
        )
    )
    _emit_maintenance_metrics(
        metrics_emitter,
        duration_seconds=duration_seconds,
        tables_processed=results["tables_processed"],
        errors=len(results["errors"]),
        snapshots_deleted=results["total_snapshots_deleted"],
    )

    return results


@dg.op
def cleanup_orphan_files(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
) -> dict[str, Any]:
    """
    Remove orphan files from all tables in the specified namespace.

    WARNING: When orphan_dry_run=False, this operation permanently deletes files
    from storage. Always test with dry_run=True first and ensure no concurrent
    writes are happening during cleanup to avoid data loss.
    """
    results = {
        "tables_processed": 0,
        "total_orphan_files": 0,
        "dry_run": config.orphan_dry_run,
        "errors": [],
    }
    operation = "cleanup_orphan_files"
    start_time = time.time()
    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=_maintenance_tags(
                config,
                operation=operation,
                dry_run=config.orphan_dry_run,
            )
        )
    )
    context.log.info(
        "Starting Iceberg maintenance operation",
        extra=_maintenance_log_extra(
            context,
            config,
            operation=operation,
            phase="start",
            dry_run=config.orphan_dry_run,
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.start",
        level="info",
        payload=_maintenance_payload(
            context,
            config,
            operation=operation,
            dry_run=config.orphan_dry_run,
        ),
    )

    if not config.orphan_dry_run:
        context.log.warning(
            "DESTRUCTIVE OPERATION: orphan_dry_run=False will DELETE files from storage. "
            "Ensure no concurrent writes are happening.",
            extra=_maintenance_log_extra(
                context,
                config,
                operation=operation,
                dry_run=config.orphan_dry_run,
            ),
        )

    if config.namespace == "all":
        namespaces = _list_namespaces(config.ref)
    else:
        namespaces = [config.namespace]

    for namespace in namespaces:
        tables = _list_tables(namespace, config.ref)
        for table_name in tables:
            try:
                result = remove_orphan_files(
                    table_name=table_name,
                    older_than_days=config.orphan_retention_days,
                    dry_run=config.orphan_dry_run,
                    ref=config.ref,
                )
                results["tables_processed"] += 1
                results["total_orphan_files"] += result["orphan_count"]
                action = "Found" if config.orphan_dry_run else "Removed"
                context.log.info(
                    f"{action} {result['orphan_count']} orphan files in {table_name}",
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        orphan_files=result["orphan_count"],
                        dry_run=config.orphan_dry_run,
                    ),
                )
            except Exception as e:
                error_msg = f"Failed to cleanup orphan files for {table_name}: {e}"
                context.log.warning(
                    error_msg,
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        dry_run=config.orphan_dry_run,
                        error=str(e),
                    ),
                )
                results["errors"].append(error_msg)

    duration_seconds = time.time() - start_time
    status = "success" if not results["errors"] else "failure"
    summary_payload = _maintenance_payload(
        context,
        config,
        operation=operation,
        status=status,
        duration_seconds=duration_seconds,
        tables_processed=results["tables_processed"],
        orphan_files=results["total_orphan_files"],
        errors=len(results["errors"]),
        dry_run=config.orphan_dry_run,
    )
    context.log.info(
        "Completed Iceberg maintenance operation",
        extra=_maintenance_log_extra(
            context,
            config,
            operation=operation,
            status=status,
            duration_seconds=duration_seconds,
            tables_processed=results["tables_processed"],
            orphan_files=results["total_orphan_files"],
            errors=len(results["errors"]),
            dry_run=config.orphan_dry_run,
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.complete",
        level="info",
        payload=summary_payload,
    )
    if results["errors"]:
        telemetry.emit_log(
            name="iceberg.maintenance.failed",
            level="error",
            payload=summary_payload,
        )
    metrics_emitter = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=_maintenance_tags(
                config,
                operation=operation,
                status=status,
                dry_run=config.orphan_dry_run,
            )
        )
    )
    _emit_maintenance_metrics(
        metrics_emitter,
        duration_seconds=duration_seconds,
        tables_processed=results["tables_processed"],
        errors=len(results["errors"]),
        orphan_files=results["total_orphan_files"],
    )

    return results


@dg.op
def collect_table_stats(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
) -> dict[str, Any]:
    """Collect statistics for all tables in the specified namespace."""
    results = {"tables": [], "total_size_mb": 0, "total_records": 0, "errors": []}
    operation = "collect_table_stats"
    start_time = time.time()
    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(tags=_maintenance_tags(config, operation=operation))
    )
    context.log.info(
        "Starting Iceberg maintenance operation",
        extra=_maintenance_log_extra(context, config, operation=operation, phase="start"),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.start",
        level="info",
        payload=_maintenance_payload(context, config, operation=operation),
    )

    if config.namespace == "all":
        namespaces = _list_namespaces(config.ref)
    else:
        namespaces = [config.namespace]

    for namespace in namespaces:
        tables = _list_tables(namespace, config.ref)
        for table_name in tables:
            try:
                stats = get_table_stats(table_name=table_name, ref=config.ref)
                results["tables"].append(stats)
                results["total_size_mb"] += stats["total_size_mb"]
                results["total_records"] += stats["total_records"]
                context.log.info(
                    f"Table {table_name}: {stats['total_records']} records, "
                    f"{stats['total_size_mb']} MB, {stats['snapshot_count']} snapshots",
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        total_records=stats["total_records"],
                        total_size_mb=stats["total_size_mb"],
                        snapshot_count=stats["snapshot_count"],
                    ),
                )
            except Exception as e:
                error_msg = f"Failed to get stats for {table_name}: {e}"
                context.log.warning(
                    error_msg,
                    extra=_maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        table_name=table_name,
                        error=str(e),
                    ),
                )
                results["errors"].append(error_msg)

    duration_seconds = time.time() - start_time
    status = "success" if not results["errors"] else "failure"
    summary_payload = _maintenance_payload(
        context,
        config,
        operation=operation,
        status=status,
        duration_seconds=duration_seconds,
        tables_processed=len(results["tables"]),
        total_records=results["total_records"],
        total_size_mb=results["total_size_mb"],
        errors=len(results["errors"]),
    )
    context.log.info(
        "Completed Iceberg maintenance operation",
        extra=_maintenance_log_extra(
            context,
            config,
            operation=operation,
            status=status,
            duration_seconds=duration_seconds,
            tables_processed=len(results["tables"]),
            total_records=results["total_records"],
            total_size_mb=results["total_size_mb"],
            errors=len(results["errors"]),
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.complete",
        level="info",
        payload=summary_payload,
    )
    if results["errors"]:
        telemetry.emit_log(
            name="iceberg.maintenance.failed",
            level="error",
            payload=summary_payload,
        )
    metrics_emitter = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=_maintenance_tags(config, operation=operation, status=status)
        )
    )
    _emit_maintenance_metrics(
        metrics_emitter,
        duration_seconds=duration_seconds,
        tables_processed=len(results["tables"]),
        errors=len(results["errors"]),
        total_records=results["total_records"],
        total_size_mb=results["total_size_mb"],
    )

    return results


@dg.job(
    description=(
        "Run all Iceberg table maintenance operations: snapshot expiration, "
        "orphan file cleanup, and table statistics collection"
    ),
)
def iceberg_maintenance_job():
    """Job that runs all maintenance operations: snapshot expiration, orphan file cleanup."""
    expire_table_snapshots()
    cleanup_orphan_files()
    collect_table_stats()


@dg.job(
    description="Expire old snapshots from Iceberg tables",
)
def expire_snapshots_job():
    """Job that only expires snapshots."""
    expire_table_snapshots()


@dg.job(
    description="Cleanup orphan files from Iceberg tables",
)
def orphan_cleanup_job():
    """Job that only cleans up orphan files."""
    cleanup_orphan_files()


@dg.job(
    description="Collect statistics for all Iceberg tables",
)
def table_stats_job():
    """Job that only collects table statistics."""
    collect_table_stats()


# Default schedule: run full maintenance daily at 2 AM
iceberg_maintenance_schedule = dg.ScheduleDefinition(
    job=iceberg_maintenance_job,
    cron_schedule="0 2 * * *",
    default_status=dg.DefaultScheduleStatus.STOPPED,
    execution_timezone="UTC",
)


def get_maintenance_definitions() -> dg.Definitions:
    """
    Get Dagster definitions for Iceberg maintenance.

    Returns definitions that can be merged into a project's main definitions.

    Example:
        ```python
        from phlo_iceberg.maintenance import get_maintenance_definitions

        # In your definitions file
        maintenance_defs = get_maintenance_definitions()
        defs = dg.Definitions.merge(your_defs, maintenance_defs)
        ```
    """
    return dg.Definitions(
        jobs=[
            iceberg_maintenance_job,
            expire_snapshots_job,
            orphan_cleanup_job,
            table_stats_job,
        ],
        schedules=[iceberg_maintenance_schedule],
    )
