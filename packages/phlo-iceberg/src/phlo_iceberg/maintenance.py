"""
Iceberg table maintenance jobs and schedules for Dagster.

Provides scheduled maintenance operations including snapshot expiration,
orphan file cleanup, and table statistics collection for Iceberg tables.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

import dagster as dg
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
                    f"Expired {result['deleted_snapshots']} snapshots from {table_name}"
                )
            except Exception as e:
                error_msg = f"Failed to expire snapshots for {table_name}: {e}"
                context.log.warning(error_msg)
                results["errors"].append(error_msg)

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

    if not config.orphan_dry_run:
        context.log.warning(
            "DESTRUCTIVE OPERATION: orphan_dry_run=False will DELETE files from storage. "
            "Ensure no concurrent writes are happening."
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
                context.log.info(f"{action} {result['orphan_count']} orphan files in {table_name}")
            except Exception as e:
                error_msg = f"Failed to cleanup orphan files for {table_name}: {e}"
                context.log.warning(error_msg)
                results["errors"].append(error_msg)

    return results


@dg.op
def collect_table_stats(
    context: dg.OpExecutionContext,
    config: MaintenanceConfig,
) -> dict[str, Any]:
    """Collect statistics for all tables in the specified namespace."""
    results = {"tables": [], "total_size_mb": 0, "total_records": 0, "errors": []}

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
                    f"{stats['total_size_mb']} MB, {stats['snapshot_count']} snapshots"
                )
            except Exception as e:
                error_msg = f"Failed to get stats for {table_name}: {e}"
                context.log.warning(error_msg)
                results["errors"].append(error_msg)

    return results


@dg.job(
    description="Run all Iceberg table maintenance operations: snapshot expiration, orphan file cleanup, and table statistics collection",
)
def iceberg_maintenance_job():
    """Job that runs all maintenance operations: snapshot expiration, orphan file cleanup, and statistics collection."""
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
