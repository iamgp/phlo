"""Shared utilities for Iceberg table maintenance operations.

This module provides common helpers used by Iceberg maintenance jobs
and sensors. It includes configuration models, telemetry tagging, logging
utilities, and catalog interaction functions.

Configuration:
    MaintenanceConfig: Pydantic model for maintenance parameters:
    - namespace: Target namespace or "all"
    - snapshot_retention_days: Age threshold for snapshot expiration
    - snapshot_retain_last: Minimum snapshots to preserve
    - orphan_retention_days: Age threshold for orphan file deletion
    - orphan_dry_run: List-only mode for orphan cleanup
    - ref: Nessie branch reference (default: main)
    - table_allowlist: Optional restriction to specific tables

Telemetry Support:
    - maintenance_tags(): Build telemetry context tags
    - maintenance_payload(): Construct structured event payloads
    - maintenance_log_extra(): Prepare logging extra fields
    - start_maintenance_op(): Emit start telemetry and logs
    - finish_maintenance_op(): Emit completion telemetry and metrics
    - emit_maintenance_metrics(): Publish standard metrics

Catalog Operations:
    - list_tables(): Get fully qualified table names in a namespace
    - list_namespaces(): Get all namespaces for a reference
    - resolve_namespaces(): Expand "all" or return specific namespace

Integration Requirements:
    Requires phlo-iceberg package for catalog operations.
    Functions lazily load dependencies for optional integration support.

Example:
    Configuration and telemetry::

        from phlo_dagster.iceberg_maintenance_utils import (
            MaintenanceConfig,
            start_maintenance_op,
            finish_maintenance_op,
        )

        config = MaintenanceConfig(
            namespace="raw",
            snapshot_retention_days=7,
            ref="main",
        )

        telemetry = start_maintenance_op(context, config, "expire_snapshots")
        # ... perform maintenance ...
        summary = finish_maintenance_op(
            context, config, telemetry, "expire_snapshots",
            duration_seconds=elapsed, errors=errors,
            tables_processed=10, snapshots_deleted=50,
        )

"""

from __future__ import annotations

from typing import Annotated, Any, Optional

import dagster as dg
from phlo.hooks import HookCorrelation, TelemetryEventContext, TelemetryEventEmitter
from pydantic import Field

from phlo.logging import get_logger

logger = get_logger(__name__)


def _load_get_catalog():
    """Load phlo-iceberg catalog helper lazily for optional integration support.

    Args:
        None

    Returns:
        get_catalog function from phlo_iceberg.catalog.

    Raises:
        RuntimeError: If phlo-iceberg package is not available.

    """
    try:
        from phlo_iceberg.catalog import get_catalog
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Iceberg maintenance requires phlo-iceberg. Install phlo-dagster[iceberg] "
            "or phlo-iceberg."
        ) from exc
    return get_catalog


class MaintenanceConfig(dg.Config):
    """Configuration for Iceberg table maintenance operations.

    Attributes:
        namespace: Namespace to run maintenance on, or ``"all"`` for all namespaces.
        snapshot_retention_days: Snapshot age threshold for expiration in days.
        snapshot_retain_last: Minimum number of snapshots to retain.
        orphan_retention_days: Orphan file age threshold for deletion in days.
        orphan_dry_run: If ``True``, list orphan files without deleting.
        ref: Nessie reference (branch or tag) used for catalog operations.

    """

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
    # Optional allowlist of fully qualified table names to restrict maintenance to
    table_allowlist: Optional[list[str]] = None


def maintenance_tags(
    config: MaintenanceConfig,
    *,
    operation: str,
    dry_run: bool | None = None,
    status: str | None = None,
) -> dict[str, str]:
    """Build telemetry tag values for a maintenance operation.

    Args:
        config: Maintenance runtime configuration.
        operation: Maintenance operation name.
        dry_run: Optional dry-run flag to include in tags.
        status: Optional operation status label.

    Returns:
        Tag dictionary suitable for telemetry event context.

    """

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
    """Build a structured telemetry payload for a maintenance operation.

    Args:
        context: Dagster operation execution context.
        config: Maintenance runtime configuration.
        operation: Maintenance operation name.
        **extra: Additional payload fields.

    Returns:
        Base payload merged with any extra fields.

    """

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
    """Build structured ``extra`` fields for maintenance log records.

    Args:
        context: Dagster operation execution context.
        config: Maintenance runtime configuration.
        operation: Maintenance operation name.
        **extra: Additional log fields.

    Returns:
        Dictionary for the logging ``extra`` parameter.

    """

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
    """Emit standard maintenance run metrics.

    Args:
        emitter: Telemetry emitter used to publish metric events.
        duration_seconds: Total operation duration.
        tables_processed: Number of tables processed.
        errors: Number of errors observed.
        snapshots_deleted: Optional number of deleted snapshots.
        orphan_files: Optional number of orphan files processed.
        total_records: Optional total records affected.
        total_size_mb: Optional total data size affected in MB.

    """

    payload = dict(emitter._context.tags)
    emitter.emit_metric(name="iceberg.maintenance.run", value=1, unit="run", payload=payload)
    emitter.emit_metric(
        name="iceberg.maintenance.duration_seconds",
        value=duration_seconds,
        unit="seconds",
        payload=payload,
    )
    emitter.emit_metric(
        name="iceberg.maintenance.tables_processed",
        value=tables_processed,
        unit="tables",
        payload=payload,
    )
    emitter.emit_metric(
        name="iceberg.maintenance.errors",
        value=errors,
        unit="errors",
        payload=payload,
    )
    if snapshots_deleted is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.snapshots_deleted",
            value=snapshots_deleted,
            unit="snapshots",
            payload=payload,
        )
    if orphan_files is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.orphan_files",
            value=orphan_files,
            unit="files",
            payload=payload,
        )
    if total_records is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.total_records",
            value=total_records,
            unit="records",
            payload=payload,
        )
    if total_size_mb is not None:
        emitter.emit_metric(
            name="iceberg.maintenance.total_size_mb",
            value=total_size_mb,
            unit="mb",
            payload=payload,
        )


def resolve_namespaces(config: MaintenanceConfig) -> list[str]:
    """Resolve configured namespace scope into a namespace list.

    Args:
        config: Maintenance runtime configuration.

    Returns:
        List of namespaces to target for maintenance.

    """

    if config.namespace == "all":
        return list_namespaces(config.ref)
    return [config.namespace]


def start_maintenance_op(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
    operation: str,
    **extra_tags: Any,
) -> TelemetryEventEmitter:
    """Emit start telemetry and logs for a maintenance operation.

    Args:
        context: Dagster operation execution context.
        config: Maintenance runtime configuration.
        operation: Maintenance operation name.
        **extra_tags: Additional tags included in telemetry context.

    Returns:
        Telemetry emitter initialized with maintenance tags.

    """

    telemetry = TelemetryEventEmitter(
        TelemetryEventContext(
            tags=maintenance_tags(config, operation=operation, **extra_tags),
            correlation=HookCorrelation(run_id=context.run_id, job_name=context.job_name),
        )
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
    evidence: dict[str, Any] | None = None,
    **metrics_kwargs: Any,
) -> dict[str, Any]:
    """Emit completion telemetry, logs, and metrics for maintenance.

    Args:
        context: Dagster operation execution context.
        config: Maintenance runtime configuration.
        telemetry: Telemetry emitter returned from operation start.
        operation: Maintenance operation name.
        duration_seconds: Total operation duration.
        errors: Collection of operation error messages.
        extra_tags: Optional extra tags for status and metrics context.
        **metrics_kwargs: Additional metric payload values.

    Returns:
        Summary payload emitted for operation completion.

    """

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
    if evidence:
        summary_payload["evidence"] = evidence
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
            tags=maintenance_tags(config, operation=operation, status=status, **tag_extras),
            correlation=HookCorrelation(run_id=context.run_id, job_name=context.job_name),
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
    """List fully qualified table names in a namespace.

    Args:
        namespace: Catalog namespace.
        ref: Nessie reference to query.

    Returns:
        Fully qualified table names, or an empty list on errors.

    """
    from pyiceberg.exceptions import NoSuchNamespaceError

    catalog = _load_get_catalog()(ref=ref)
    try:
        tables = catalog.list_tables(namespace)
        return [f"{namespace}.{table[1]}" for table in tables]
    except NoSuchNamespaceError:
        logger.info("namespace_not_found_skipping", namespace=namespace)
        return []
    except Exception:
        logger.exception("list_tables_failed", namespace=namespace)
        return []


def list_namespaces(ref: str) -> list[str]:
    """List catalog namespaces for a Nessie reference.

    Args:
        ref: Nessie reference to query.

    Returns:
        Namespace names, or an empty list on errors.

    """

    catalog = _load_get_catalog()(ref=ref)
    try:
        namespaces = catalog.list_namespaces()
        return [ns[0] for ns in namespaces]
    except Exception:
        logger.exception("Failed to list namespaces")
        return []
