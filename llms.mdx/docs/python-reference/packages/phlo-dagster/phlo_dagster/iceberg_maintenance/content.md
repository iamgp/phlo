# iceberg_maintenance (/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance)



Iceberg table maintenance jobs and schedules for Dagster.

This module provides scheduled and on-demand maintenance operations for
Apache Iceberg tables through Dagster jobs and ops. It handles snapshot
expiration, orphan file cleanup, and table statistics collection.

Maintenance Operations:

* expire\_table\_snapshots: Remove old snapshots based on retention policy
* cleanup\_orphan\_files: Delete unreferenced data files (with dry-run support)
* collect\_table\_stats: Gather table metadata for monitoring and policy evaluation

Jobs Provided:

* iceberg\_maintenance\_job: Runs all maintenance operations
* expire\_snapshots\_job: Snapshot expiration only
* orphan\_cleanup\_job: Orphan file cleanup only
* table\_stats\_job: Statistics collection only

Schedule:
Default schedule runs full maintenance daily at 2 AM UTC (stopped by default).

Safety Features:

* Dry-run mode for orphan file cleanup (orphan\_dry\_run=True)
* Destructive operation warnings in logs
* Table allowlist for targeted maintenance
* Error collection and reporting without failing entire job

Configuration:
Uses MaintenanceConfig with fields:

* namespace: Target namespace (or "all")
* snapshot\_retention\_days: Age threshold for snapshots
* snapshot\_retain\_last: Minimum snapshots to keep
* orphan\_retention\_days: Age threshold for orphan files
* orphan\_dry\_run: List-only mode for orphan cleanup
* ref: Nessie branch reference

Integration Requirements:
Requires phlo-iceberg package for table operations.

Example:
Including maintenance in definitions::

from phlo\_dagster.iceberg\_maintenance import get\_maintenance\_definitions

maintenance\_defs = get\_maintenance\_definitions()
defs = dg.Definitions.merge(your\_defs, maintenance\_defs)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;iceberg_maintenance_schedule&#x22;" type="null" value="&#x22;dg.ScheduleDefinition(job=iceberg_maintenance_job, cron_schedule='0 2 * * *', default_status=(dg.DefaultScheduleStatus.STOPPED), execution_timezone='UTC')&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_iceberg_maintenance_functions&#x22;" type="&#x22;() -> tuple[Any, Any, Any]&#x22;">
      Load iceberg maintenance helpers lazily for optional integration support.

      <PySourceCode>
        ```python
        def _load_iceberg_maintenance_functions() -> tuple[Any, Any, Any]:
            """Load iceberg maintenance helpers lazily for optional integration support.

            Args:
                None

            Returns:
                Tuple of (expire_snapshots, get_table_stats, remove_orphan_files) functions.

            Raises:
                RuntimeError: If phlo-iceberg package is not available.

            """
            try:
                from phlo_iceberg.tables import expire_snapshots, get_table_stats, remove_orphan_files
            except Exception as exc:  # noqa: BLE001 - runtime guidance for optional dependency
                raise RuntimeError(
                    "Iceberg maintenance requires phlo-iceberg. Install phlo-dagster[iceberg] "
                    "or phlo-iceberg."
                ) from exc
            return expire_snapshots, get_table_stats, remove_orphan_files
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        Tuple of (expire\_snapshots, get\_table\_stats, remove\_orphan\_files) functions.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;expire_table_snapshots&#x22;" type="&#x22;(context, config) -> dict[str, Any]&#x22;">
      Expire old snapshots from all tables in the specified namespace.

      <PySourceCode>
        ```python
        @dg.op
        def expire_table_snapshots(
            context: dg.OpExecutionContext,
            config: MaintenanceConfig,
        ) -> dict[str, Any]:
            """Expire old snapshots from all tables in the specified namespace.

            Args:
                context: Dagster operation execution context.
                config: Maintenance configuration.

            Returns:
                Summary dict with tables_processed, total_snapshots_deleted, errors.

            Raises:
                No explicit exceptions raised. Logs warnings on table failures.

            """
            tables_processed = 0
            total_snapshots_deleted = 0
            errors: list[str] = []
            operation = "expire_snapshots"
            start_time = time.time()
            telemetry = start_maintenance_op(context, config, operation)
            expire_snapshots, _, _ = _load_iceberg_maintenance_functions()

            for namespace in resolve_namespaces(config):
                for table_name in list_tables(namespace, config.ref):
                    if config.table_allowlist and table_name not in config.table_allowlist:
                        continue
                    try:
                        result = expire_snapshots(
                            table_name=table_name,
                            older_than_days=config.snapshot_retention_days,
                            retain_last=config.snapshot_retain_last,
                            ref=config.ref,
                        )
                        tables_processed += 1
                        total_snapshots_deleted += result["deleted_snapshots"]
                        context.log.info(
                            f"Expired {result['deleted_snapshots']} snapshots from {table_name}",
                            extra=maintenance_log_extra(
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
                            extra=maintenance_log_extra(
                                context,
                                config,
                                operation=operation,
                                table_name=table_name,
                                error=str(e),
                            ),
                        )
                        errors.append(error_msg)

            summary_payload = finish_maintenance_op(
                context,
                config,
                telemetry,
                operation,
                duration_seconds=time.time() - start_time,
                errors=errors,
                tables_processed=tables_processed,
                snapshots_deleted=total_snapshots_deleted,
            )
            summary_payload.update(
                {
                    "tables_processed": tables_processed,
                    "total_snapshots_deleted": total_snapshots_deleted,
                    "errors": errors,
                }
            )
            return summary_payload
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Summary dict with tables\_processed, total\_snapshots\_deleted, errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;cleanup_orphan_files&#x22;" type="&#x22;(context, config) -> dict[str, Any]&#x22;">
      Remove orphan files from all tables in the specified namespace.

      WARNING: When orphan\_dry\_run=False, this operation permanently deletes files
      from storage. Always test with dry\_run=True first and ensure no concurrent
      writes are happening during cleanup to avoid data loss.

      <PySourceCode>
        ```python
        @dg.op
        def cleanup_orphan_files(
            context: dg.OpExecutionContext,
            config: MaintenanceConfig,
        ) -> dict[str, Any]:
            """Remove orphan files from all tables in the specified namespace.

            WARNING: When orphan_dry_run=False, this operation permanently deletes files
            from storage. Always test with dry_run=True first and ensure no concurrent
            writes are happening during cleanup to avoid data loss.

            Args:
                context: Dagster operation execution context.
                config: Maintenance configuration.

            Returns:
                Results dict with tables_processed, total_orphan_files, dry_run, errors.

            Raises:
                No explicit exceptions raised. Logs warnings on table failures.

            """
            tables_processed = 0
            total_orphan_files = 0
            errors: list[str] = []
            results: dict[str, Any] = {
                "tables_processed": tables_processed,
                "total_orphan_files": total_orphan_files,
                "dry_run": config.orphan_dry_run,
                "errors": errors,
            }
            operation = "cleanup_orphan_files"
            start_time = time.time()
            telemetry = start_maintenance_op(context, config, operation, dry_run=config.orphan_dry_run)
            _, _, remove_orphan_files = _load_iceberg_maintenance_functions()

            if not config.orphan_dry_run:
                context.log.warning(
                    "DESTRUCTIVE OPERATION: orphan_dry_run=False will DELETE files from storage. "
                    "Ensure no concurrent writes are happening.",
                    extra=maintenance_log_extra(
                        context,
                        config,
                        operation=operation,
                        dry_run=config.orphan_dry_run,
                    ),
                )

            for namespace in resolve_namespaces(config):
                for table_name in list_tables(namespace, config.ref):
                    if config.table_allowlist and table_name not in config.table_allowlist:
                        continue
                    try:
                        result = remove_orphan_files(
                            table_name=table_name,
                            older_than_days=config.orphan_retention_days,
                            dry_run=config.orphan_dry_run,
                            ref=config.ref,
                        )
                        tables_processed += 1
                        orphan_count = int(result.get("orphan_count", 0) or 0)
                        total_orphan_files += orphan_count
                        action = "Found" if config.orphan_dry_run else "Removed"
                        context.log.info(
                            f"{action} {orphan_count} orphan files in {table_name}",
                            extra=maintenance_log_extra(
                                context,
                                config,
                                operation=operation,
                                table_name=table_name,
                                orphan_files=orphan_count,
                                dry_run=config.orphan_dry_run,
                            ),
                        )
                    except Exception as e:
                        error_msg = f"Failed to cleanup orphan files for {table_name}: {e}"
                        context.log.warning(
                            error_msg,
                            extra=maintenance_log_extra(
                                context,
                                config,
                                operation=operation,
                                table_name=table_name,
                                dry_run=config.orphan_dry_run,
                                error=str(e),
                            ),
                        )
                        errors.append(error_msg)

            finish_maintenance_op(
                context,
                config,
                telemetry,
                operation,
                duration_seconds=time.time() - start_time,
                errors=errors,
                extra_tags={"dry_run": config.orphan_dry_run},
                tables_processed=tables_processed,
                orphan_files=total_orphan_files,
            )

            results["tables_processed"] = tables_processed
            results["total_orphan_files"] = total_orphan_files
            results["errors"] = errors

            return results
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Results dict with tables\_processed, total\_orphan\_files, dry\_run, errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;collect_table_stats&#x22;" type="&#x22;(context, config) -> dict[str, Any]&#x22;">
      Collect statistics for all tables in the specified namespace.

      <PySourceCode>
        ```python
        @dg.op
        def collect_table_stats(
            context: dg.OpExecutionContext,
            config: MaintenanceConfig,
        ) -> dict[str, Any]:
            """Collect statistics for all tables in the specified namespace.

            Args:
                context: Dagster operation execution context.
                config: Maintenance configuration.

            Returns:
                Results dict with tables, total_size_mb, total_records, errors.

            Raises:
                No explicit exceptions raised. Logs warnings on table failures.

            """
            tables: list[dict[str, Any]] = []
            total_size_mb = 0.0
            total_records = 0
            errors: list[str] = []
            results: dict[str, Any] = {
                "tables": tables,
                "total_size_mb": total_size_mb,
                "total_records": total_records,
                "errors": errors,
            }
            operation = "collect_table_stats"
            start_time = time.time()
            telemetry = start_maintenance_op(context, config, operation)
            _, get_table_stats, _ = _load_iceberg_maintenance_functions()

            for namespace in resolve_namespaces(config):
                for table_name in list_tables(namespace, config.ref):
                    if config.table_allowlist and table_name not in config.table_allowlist:
                        continue
                    try:
                        stats = get_table_stats(table_name=table_name, ref=config.ref)
                        tables.append(stats)
                        total_size_mb += stats["total_size_mb"]
                        total_records += stats["total_records"]
                        context.log.info(
                            f"Table {table_name}: {stats['total_records']} records, "
                            f"{stats['total_size_mb']} MB, {stats['snapshot_count']} snapshots",
                            extra=maintenance_log_extra(
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
                            extra=maintenance_log_extra(
                                context,
                                config,
                                operation=operation,
                                table_name=table_name,
                                error=str(e),
                            ),
                        )
                        errors.append(error_msg)

            finish_maintenance_op(
                context,
                config,
                telemetry,
                operation,
                duration_seconds=time.time() - start_time,
                errors=errors,
                tables_processed=len(tables),
                total_records=total_records,
                total_size_mb=total_size_mb,
            )

            results["tables"] = tables
            results["total_size_mb"] = total_size_mb
            results["total_records"] = total_records
            results["errors"] = errors

            return results
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Results dict with tables, total\_size\_mb, total\_records, errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;iceberg_maintenance_job&#x22;" type="&#x22;()&#x22;">
      Job that runs all maintenance operations: snapshot expiration, orphan file cleanup.

      <PySourceCode>
        ```python
        @dg.job(
            description=(
                "Run all Iceberg table maintenance operations: snapshot expiration, "
                "orphan file cleanup, and table statistics collection"
            ),
        )
        def iceberg_maintenance_job():
            """Job that runs all maintenance operations: snapshot expiration, orphan file cleanup.

            Args:
                None

            Returns:
                None

            Raises:
                No explicit exceptions raised.

            """
            expire_table_snapshots()
            cleanup_orphan_files()
            collect_table_stats()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;expire_snapshots_job&#x22;" type="&#x22;()&#x22;">
      Job that only expires snapshots.

      <PySourceCode>
        ```python
        @dg.job(
            description="Expire old snapshots from Iceberg tables",
        )
        def expire_snapshots_job():
            """Job that only expires snapshots.

            Args:
                None

            Returns:
                None

            Raises:
                No explicit exceptions raised.

            """
            expire_table_snapshots()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;orphan_cleanup_job&#x22;" type="&#x22;()&#x22;">
      Job that only cleans up orphan files.

      <PySourceCode>
        ```python
        @dg.job(
            description="Cleanup orphan files from Iceberg tables",
        )
        def orphan_cleanup_job():
            """Job that only cleans up orphan files.

            Args:
                None

            Returns:
                None

            Raises:
                No explicit exceptions raised.

            """
            cleanup_orphan_files()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;table_stats_job&#x22;" type="&#x22;()&#x22;">
      Job that only collects table statistics.

      <PySourceCode>
        ```python
        @dg.job(
            description="Collect statistics for all Iceberg tables",
        )
        def table_stats_job():
            """Job that only collects table statistics.

            Args:
                None

            Returns:
                None

            Raises:
                No explicit exceptions raised.

            """
            collect_table_stats()
        ```
      </PySourceCode>

      <PyFunctionReturn type="null">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_maintenance_definitions&#x22;" type="&#x22;() -> dg.Definitions&#x22;">
      Get Dagster definitions for Iceberg maintenance.

      Returns definitions that can be merged into a project's main definitions.

      <PySourceCode>
        ```python
        def get_maintenance_definitions() -> dg.Definitions:
            """Get Dagster definitions for Iceberg maintenance.

            Returns definitions that can be merged into a project's main definitions.

            Args:
                None

            Returns:
                Dagster Definitions containing maintenance jobs and schedules.

            Raises:
                No explicit exceptions raised.

            """
            logger.info(
                "dagster_iceberg_maintenance_definitions_built",
                job_count=4,
                schedule_count=1,
            )
            return dg.Definitions(
                jobs=[
                    iceberg_maintenance_job,
                    expire_snapshots_job,
                    orphan_cleanup_job,
                    table_stats_job,
                ],
                schedules=[iceberg_maintenance_schedule],
            )
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dagster.Definitions&#x22;">
        Dagster Definitions containing maintenance jobs and schedules.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
