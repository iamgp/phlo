# maintenance (/docs/python-reference/packages/phlo-api/phlo_api/api/maintenance)



Maintenance API Router.

Endpoints for Iceberg maintenance observability data.

This module provides API endpoints for querying maintenance operation status
and metrics from the maintenance read-model capability. It enables monitoring
of data lifecycle operations like compaction, cleanup, and optimization.

Key Endpoints:
GET /status: Get maintenance status snapshot.
GET /metrics: Get Prometheus-formatted maintenance metrics.

Environment Variables:
PHLO\_MAINTENANCE\_READ\_MODEL: Name of the maintenance read model provider.

Example:
Querying maintenance status:

.. code-block:: bash

curl [http://localhost:4000/api/maintenance/status](http://localhost:4000/api/maintenance/status)

Response:

.. code-block:: json

\{
"last\_updated": "2024-01-15T10:30:00",
"operations": \[
\{
"operation": "OPTIMIZE",
"namespace": "warehouse",
"ref": "main",
"status": "COMPLETED"
}
]
}

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;router&#x22;" type="null" value="&#x22;APIRouter(tags=['maintenance'])&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MaintenanceOperationStatus&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/maintenance/MaintenanceOperationStatus&#x22;" />

      <Card title="&#x22;MaintenanceStatusSnapshot&#x22;" href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/api/maintenance/MaintenanceStatusSnapshot&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_maintenance_read_model&#x22;" type="&#x22;() -> MaintenanceReadModel&#x22;">
      Resolve the configured maintenance read-model capability.

      <PySourceCode>
        ```python
        def _resolve_maintenance_read_model() -> MaintenanceReadModel:
            """Resolve the configured maintenance read-model capability."""
            discover_capabilities()
            name = os.environ.get(_DEFAULT_READ_MODEL_ENV)
            resolution = resolve_capability("maintenance_read_model", name)
            if resolution is None:
                available = list_capabilities("maintenance_read_model")
                if name:
                    raise RuntimeError(
                        f"Maintenance read model '{name}' not found. Available providers: {available}"
                    )
                if available:
                    raise RuntimeError(
                        "Multiple maintenance_read_model providers are installed. "
                        f"Set {_DEFAULT_READ_MODEL_ENV} to select one: {available}"
                    )
                raise RuntimeError(
                    "Maintenance observability requires a maintenance_read_model capability. "
                    "Install the core maintenance provider or another provider."
                )
            return resolution.provider
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo.capabilities.MaintenanceReadModel&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_maintenance_status&#x22;" type="&#x22;() -> MaintenanceStatusSnapshot | dict[str, str]&#x22;">
      Get maintenance status derived from telemetry logs.

      Returns the current maintenance operation snapshot from the read model.

      <PySourceCode>
        ```python
        @router.get("/status", response_model=MaintenanceStatusSnapshot | dict)
        def get_maintenance_status() -> MaintenanceStatusSnapshot | dict[str, str]:
            """Get maintenance status derived from telemetry logs.

            Returns the current maintenance operation snapshot from the read model.

            Args:
                None: No arguments required.

            Returns:
                MaintenanceStatusSnapshot with operations and timestamp, or error dictionary.

            Raises:
                None: Exceptions are caught and returned in the response.

            """
            try:
                snapshot = _resolve_maintenance_read_model().load_maintenance_status()
                logger.debug("maintenance_status_loaded", operation_count=len(snapshot.operations))
                return _serialize_snapshot(snapshot)
            except Exception as exc:
                logger.exception("maintenance_status_load_failed")
                return {"error": str(exc)}
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;MaintenanceStatusSnapshot | dict[str, str]&#x22;">
        MaintenanceStatusSnapshot with operations and timestamp, or error dictionary.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_maintenance_metrics&#x22;" type="&#x22;() -> PlainTextResponse&#x22;">
      Expose maintenance metrics in Prometheus text format.

      Returns maintenance operation metrics formatted for Prometheus scraping.

      <PySourceCode>
        ```python
        @router.get("/metrics", response_class=PlainTextResponse)
        def get_maintenance_metrics() -> PlainTextResponse:
            """Expose maintenance metrics in Prometheus text format.

            Returns maintenance operation metrics formatted for Prometheus scraping.

            Args:
                None: No arguments required.

            Returns:
                PlainTextResponse with Prometheus-formatted metrics.

            Raises:
                None: Exceptions are caught and returned with status 500.

            """
            try:
                metrics_payload = _resolve_maintenance_read_model().render_maintenance_prometheus()
                logger.debug("maintenance_metrics_rendered", payload_length=len(metrics_payload))
                return PlainTextResponse(metrics_payload)
            except Exception as exc:
                logger.exception("maintenance_metrics_render_failed")
                return PlainTextResponse(f"# error: {exc}\n", status_code=500)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;fastapi.responses.PlainTextResponse&#x22;">
        PlainTextResponse with Prometheus-formatted metrics.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_serialize_snapshot&#x22;" type="&#x22;(snapshot) -> MaintenanceStatusSnapshot&#x22;">
      Convert domain snapshot data into API response format.

      <PySourceCode>
        ```python
        def _serialize_snapshot(snapshot: Any) -> MaintenanceStatusSnapshot:
            """Convert domain snapshot data into API response format."""
            return MaintenanceStatusSnapshot(
                last_updated=_isoformat(snapshot.last_updated),
                operations=[_serialize_operation(op) for op in snapshot.operations],
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;snapshot&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.api.maintenance.MaintenanceStatusSnapshot&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_serialize_operation&#x22;" type="&#x22;(operation) -> MaintenanceOperationStatus&#x22;">
      Convert a maintenance operation record into API response format.

      <PySourceCode>
        ```python
        def _serialize_operation(operation: Any) -> MaintenanceOperationStatus:
            """Convert a maintenance operation record into API response format."""
            return MaintenanceOperationStatus(
                operation=operation.operation,
                namespace=operation.namespace,
                ref=operation.ref,
                status=operation.status,
                completed_at=_isoformat(operation.completed_at),
                duration_seconds=operation.duration_seconds,
                tables_processed=operation.tables_processed,
                errors=operation.errors,
                snapshots_deleted=operation.snapshots_deleted,
                orphan_files=operation.orphan_files,
                total_records=operation.total_records,
                total_size_mb=operation.total_size_mb,
                dry_run=operation.dry_run,
                run_id=operation.run_id,
                job_name=operation.job_name,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;operation&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;phlo_api.api.maintenance.MaintenanceOperationStatus&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_isoformat&#x22;" type="&#x22;(value) -> str&#x22;">
      Return an ISO timestamp when possible, else a string conversion.

      <PySourceCode>
        ```python
        def _isoformat(value: datetime | Any) -> str:
            """Return an ISO timestamp when possible, else a string conversion."""
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;datetime | Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
