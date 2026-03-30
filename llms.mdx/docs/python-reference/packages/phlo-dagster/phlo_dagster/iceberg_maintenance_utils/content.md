# iceberg_maintenance_utils (/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance_utils)



Shared utilities for Iceberg table maintenance operations.

This module provides common helpers used by Iceberg maintenance jobs
and sensors. It includes configuration models, telemetry tagging, logging
utilities, and catalog interaction functions.

Configuration:
MaintenanceConfig: Pydantic model for maintenance parameters:

* namespace: Target namespace or "all"
* snapshot\_retention\_days: Age threshold for snapshot expiration
* snapshot\_retain\_last: Minimum snapshots to preserve
* orphan\_retention\_days: Age threshold for orphan file deletion
* orphan\_dry\_run: List-only mode for orphan cleanup
* ref: Nessie branch reference (default: main)
* table\_allowlist: Optional restriction to specific tables

Telemetry Support:

* maintenance\_tags(): Build telemetry context tags
* maintenance\_payload(): Construct structured event payloads
* maintenance\_log\_extra(): Prepare logging extra fields
* start\_maintenance\_op(): Emit start telemetry and logs
* finish\_maintenance\_op(): Emit completion telemetry and metrics
* emit\_maintenance\_metrics(): Publish standard metrics

Catalog Operations:

* list\_tables(): Get fully qualified table names in a namespace
* list\_namespaces(): Get all namespaces for a reference
* resolve\_namespaces(): Expand "all" or return specific namespace

Integration Requirements:
Requires phlo-iceberg package for catalog operations.
Functions lazily load dependencies for optional integration support.

Example:
Configuration and telemetry::

from phlo\_dagster.iceberg\_maintenance\_utils import (
MaintenanceConfig,
start\_maintenance\_op,
finish\_maintenance\_op,
)

config = MaintenanceConfig(
namespace="raw",
snapshot\_retention\_days=7,
ref="main",
)

telemetry = start\_maintenance\_op(context, config, "expire\_snapshots")

... perform maintenance ... [#-perform-maintenance-]

summary = finish\_maintenance\_op(
context, config, telemetry, "expire\_snapshots",
duration\_seconds=elapsed, errors=errors,
tables\_processed=10, snapshots\_deleted=50,
)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MaintenanceConfig&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance_utils/MaintenanceConfig&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_get_catalog&#x22;" type="&#x22;()&#x22;">
      Load phlo-iceberg catalog helper lazily for optional integration support.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <PyFunctionReturn type="null">
        get\_catalog function from phlo\_iceberg.catalog.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;maintenance_tags&#x22;" type="&#x22;(config, *, operation, dry_run=None, status=None) -> dict[str, str]&#x22;">
      Build telemetry tag values for a maintenance operation.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>

        <PyParameter name="&#x22;operation&#x22;" type="&#x22;str&#x22;" value="undefined">
          Maintenance operation name.
        </PyParameter>

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool | None&#x22;" value="&#x22;None&#x22;">
          Optional dry-run flag to include in tags.
        </PyParameter>

        <PyParameter name="&#x22;status&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional operation status label.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Tag dictionary suitable for telemetry event context.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;maintenance_payload&#x22;" type="&#x22;(context, config, *, operation, **extra) -> dict[str, Any]&#x22;">
      Build a structured telemetry payload for a maintenance operation.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>

        <PyParameter name="&#x22;operation&#x22;" type="&#x22;str&#x22;" value="undefined">
          Maintenance operation name.
        </PyParameter>

        <PyParameter name="&#x22;extra&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Base payload merged with any extra fields.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;maintenance_log_extra&#x22;" type="&#x22;(context, config, *, operation, **extra) -> dict[str, Any]&#x22;">
      Build structured `extra` fields for maintenance log records.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>

        <PyParameter name="&#x22;operation&#x22;" type="&#x22;str&#x22;" value="undefined">
          Maintenance operation name.
        </PyParameter>

        <PyParameter name="&#x22;extra&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary for the logging `extra` parameter.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;emit_maintenance_metrics&#x22;" type="&#x22;(emitter, *, duration_seconds, tables_processed, errors, snapshots_deleted=None, orphan_files=None, total_records=None, total_size_mb=None) -> None&#x22;">
      Emit standard maintenance run metrics.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;emitter&#x22;" type="&#x22;TelemetryEventEmitter&#x22;" value="undefined">
          Telemetry emitter used to publish metric events.
        </PyParameter>

        <PyParameter name="&#x22;duration_seconds&#x22;" type="&#x22;float&#x22;" value="undefined">
          Total operation duration.
        </PyParameter>

        <PyParameter name="&#x22;tables_processed&#x22;" type="&#x22;int&#x22;" value="undefined">
          Number of tables processed.
        </PyParameter>

        <PyParameter name="&#x22;errors&#x22;" type="&#x22;int&#x22;" value="undefined">
          Number of errors observed.
        </PyParameter>

        <PyParameter name="&#x22;snapshots_deleted&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
          Optional number of deleted snapshots.
        </PyParameter>

        <PyParameter name="&#x22;orphan_files&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
          Optional number of orphan files processed.
        </PyParameter>

        <PyParameter name="&#x22;total_records&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
          Optional total records affected.
        </PyParameter>

        <PyParameter name="&#x22;total_size_mb&#x22;" type="&#x22;float | None&#x22;" value="&#x22;None&#x22;">
          Optional total data size affected in MB.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;resolve_namespaces&#x22;" type="&#x22;(config) -> list[str]&#x22;">
      Resolve configured namespace scope into a namespace list.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of namespaces to target for maintenance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;start_maintenance_op&#x22;" type="&#x22;(context, config, operation, **extra_tags) -> TelemetryEventEmitter&#x22;">
      Emit start telemetry and logs for a maintenance operation.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>

        <PyParameter name="&#x22;operation&#x22;" type="&#x22;str&#x22;" value="undefined">
          Maintenance operation name.
        </PyParameter>

        <PyParameter name="&#x22;extra_tags&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.hooks.TelemetryEventEmitter&#x22;">
        Telemetry emitter initialized with maintenance tags.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;finish_maintenance_op&#x22;" type="&#x22;(context, config, telemetry, operation, *, duration_seconds, errors, extra_tags=None, **metrics_kwargs) -> dict[str, Any]&#x22;">
      Emit completion telemetry, logs, and metrics for maintenance.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;dg.OpExecutionContext&#x22;" value="undefined">
          Dagster operation execution context.
        </PyParameter>

        <PyParameter name="&#x22;config&#x22;" type="&#x22;MaintenanceConfig&#x22;" value="undefined">
          Maintenance runtime configuration.
        </PyParameter>

        <PyParameter name="&#x22;telemetry&#x22;" type="&#x22;TelemetryEventEmitter&#x22;" value="undefined">
          Telemetry emitter returned from operation start.
        </PyParameter>

        <PyParameter name="&#x22;operation&#x22;" type="&#x22;str&#x22;" value="undefined">
          Maintenance operation name.
        </PyParameter>

        <PyParameter name="&#x22;duration_seconds&#x22;" type="&#x22;float&#x22;" value="undefined">
          Total operation duration.
        </PyParameter>

        <PyParameter name="&#x22;errors&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          Collection of operation error messages.
        </PyParameter>

        <PyParameter name="&#x22;extra_tags&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
          Optional extra tags for status and metrics context.
        </PyParameter>

        <PyParameter name="&#x22;metrics_kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Summary payload emitted for operation completion.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;list_tables&#x22;" type="&#x22;(namespace, ref) -> list[str]&#x22;">
      List fully qualified table names in a namespace.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;namespace&#x22;" type="&#x22;str&#x22;" value="undefined">
          Catalog namespace.
        </PyParameter>

        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="undefined">
          Nessie reference to query.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Fully qualified table names, or an empty list on errors.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;list_namespaces&#x22;" type="&#x22;(ref) -> list[str]&#x22;">
      List catalog namespaces for a Nessie reference.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="undefined">
          Nessie reference to query.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Namespace names, or an empty list on errors.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
