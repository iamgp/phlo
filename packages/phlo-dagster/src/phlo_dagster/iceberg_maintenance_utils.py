"""
Shared helpers for Iceberg table maintenance operations.

Provides configuration, tagging, payload construction, logging helpers,
metrics emission, and catalog listing utilities used by maintenance ops.
"""

from __future__ import annotations

from typing import Annotated, Any

import dagster as dg
from phlo.hooks import TelemetryEventContext, TelemetryEventEmitter
from pydantic import Field

from phlo.logging import get_logger
from phlo_iceberg.catalog import get_catalog

logger = get_logger(__name__)


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


def maintenance_tags(
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


def maintenance_payload(
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


def maintenance_log_extra(
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


def emit_maintenance_metrics(
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


def resolve_namespaces(config: MaintenanceConfig) -> list[str]:
    """Resolve namespace config to a list of namespaces."""
    if config.namespace == "all":
        return list_namespaces(config.ref)
    return [config.namespace]


def start_maintenance_op(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
    operation: str,
    **extra_tags: Any,
) -> TelemetryEventEmitter:
    """Emit start telemetry/logging for a maintenance op. Returns the emitter."""
    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(tags=maintenance_tags(config, operation=operation, **extra_tags))
    )
    context.log.info(
        "Starting Iceberg maintenance operation",
        extra=maintenance_log_extra(
            context, config, operation=operation, phase="start", **extra_tags
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.start",
        level="info",
        payload=maintenance_payload(context, config, operation=operation, **extra_tags),
    )
    return telemetry


def finish_maintenance_op(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
    telemetry: TelemetryEventEmitter,
    operation: str,
    *,
    duration_seconds: float,
    errors: list[str],
    extra_tags: dict[str, Any] | None = None,
    **metrics_kwargs: Any,
) -> dict[str, Any]:
    """Emit completion telemetry/logging/metrics. Returns the summary payload."""
    tag_extras = extra_tags or {}
    status = "success" if not errors else "failure"
    summary_payload = maintenance_payload(
        context,
        config,
        operation=operation,
        status=status,
        duration_seconds=duration_seconds,
        errors=len(errors),
        **tag_extras,
        **metrics_kwargs,
    )
    context.log.info(
        "Completed Iceberg maintenance operation",
        extra=maintenance_log_extra(
            context,
            config,
            operation=operation,
            status=status,
            duration_seconds=duration_seconds,
            errors=len(errors),
            **tag_extras,
            **metrics_kwargs,
        ),
    )
    telemetry.emit_log(
        name="iceberg.maintenance.complete",
        level="info",
        payload=summary_payload,
    )
    if errors:
        telemetry.emit_log(
            name="iceberg.maintenance.failed",
            level="error",
            payload=summary_payload,
        )
    metrics_emitter = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=maintenance_tags(config, operation=operation, status=status, **tag_extras)
        )
    )
    emit_maintenance_metrics(
        metrics_emitter,
        duration_seconds=duration_seconds,
        errors=len(errors),
        **metrics_kwargs,
    )
    return summary_payload


def list_tables(namespace: str, ref: str) -> list[str]:
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


def list_namespaces(ref: str) -> list[str]:
    """List all namespaces."""
    catalog = get_catalog(ref=ref)
    try:
        namespaces = catalog.list_namespaces()
        return [ns[0] for ns in namespaces]
    except Exception:
        logger.exception("Failed to list namespaces")
        return []
