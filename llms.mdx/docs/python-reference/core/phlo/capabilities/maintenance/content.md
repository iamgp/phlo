# maintenance (/docs/python-reference/core/phlo/capabilities/maintenance)



Default maintenance read-model implementation.

<PyAttribute name="&#x22;MAINTENANCE_COMPLETE_EVENT&#x22;" type="null" value="&#x22;'iceberg.maintenance.complete'&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;MaintenanceOperationStatus&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/maintenance/MaintenanceOperationStatus&#x22;" />

      <Card title="&#x22;MaintenanceStatusSnapshot&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/maintenance/MaintenanceStatusSnapshot&#x22;" />

      <Card title="&#x22;_PrometheusMetric&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/maintenance/_PrometheusMetric&#x22;" />

      <Card title="&#x22;DefaultMaintenanceReadModel&#x22;" href="&#x22;/docs/python-reference/core/phlo/capabilities/maintenance/DefaultMaintenanceReadModel&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;load_maintenance_status&#x22;" type="&#x22;(path=None) -> MaintenanceStatusSnapshot&#x22;">
      Load latest maintenance status per operation from telemetry events.

      <PySourceCode>
        ```python
        def load_maintenance_status(path: Path | None = None) -> MaintenanceStatusSnapshot:
            """Load latest maintenance status per operation from telemetry events."""
            event_path = get_telemetry_path(path)
            latest: dict[tuple[str, str, str], MaintenanceOperationStatus] = {}
            try:
                for event in _iter_events(event_path):
                    if event.get("event_type") != "telemetry.log":
                        continue
                    if event.get("name") != MAINTENANCE_COMPLETE_EVENT:
                        continue
                    tags = _ensure_dict(event.get("tags"))
                    payload = _ensure_dict(event.get("payload"))
                    completed_at = _parse_timestamp(event.get("timestamp"))
                    operation = _coerce_str(tags.get("operation") or payload.get("operation"), "unknown")
                    namespace = _coerce_str(tags.get("namespace") or payload.get("namespace"), "unknown")
                    ref = _coerce_str(tags.get("ref") or payload.get("ref"), "main")
                    key = (operation, namespace, ref)
                    entry = MaintenanceOperationStatus(
                        operation=operation,
                        namespace=namespace,
                        ref=ref,
                        status=_coerce_str(payload.get("status"), "unknown"),
                        completed_at=completed_at,
                        duration_seconds=_coerce_float(payload.get("duration_seconds")),
                        tables_processed=_coerce_int(payload.get("tables_processed")),
                        errors=_coerce_int(payload.get("errors")),
                        snapshots_deleted=_coerce_int(payload.get("snapshots_deleted")),
                        orphan_files=_coerce_int(payload.get("orphan_files")),
                        total_records=_coerce_int(payload.get("total_records")),
                        total_size_mb=_coerce_float(payload.get("total_size_mb")) or 0.0,
                        dry_run=_coerce_bool(tags.get("dry_run") or payload.get("dry_run")),
                        run_id=_coerce_optional_str(payload.get("run_id")),
                        job_name=_coerce_optional_str(payload.get("job_name")),
                    )
                    previous = latest.get(key)
                    if not previous or entry.completed_at > previous.completed_at:
                        latest[key] = entry
            except Exception:
                logger.warning(
                    "maintenance_status_load_failed", telemetry_path=str(event_path), exc_info=True
                )
                raise

            operations = sorted(latest.values(), key=lambda item: item.completed_at, reverse=True)
            last_updated = operations[0].completed_at if operations else datetime.now(UTC)
            return MaintenanceStatusSnapshot(last_updated=last_updated, operations=operations)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.maintenance.MaintenanceStatusSnapshot&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;render_maintenance_prometheus&#x22;" type="&#x22;(path=None) -> str&#x22;">
      Render maintenance telemetry as Prometheus text exposition.

      <PySourceCode>
        ```python
        def render_maintenance_prometheus(path: Path | None = None) -> str:
            """Render maintenance telemetry as Prometheus text exposition."""
            event_path = get_telemetry_path(path)
            counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
            gauges: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, datetime]] = {}
            try:
                for event in _iter_events(event_path):
                    if event.get("event_type") != "telemetry.metric":
                        continue
                    name = event.get("name")
                    if not isinstance(name, str):
                        continue
                    metric = _PROMETHEUS_MAP.get(name)
                    if not metric:
                        continue
                    value = _coerce_float(event.get("value"))
                    if value is None:
                        continue
                    tags = _ensure_dict(event.get("tags"))
                    labels = _metric_labels(tags)
                    label_key = tuple(sorted(labels.items()))
                    if metric.mode == "counter":
                        counters[(metric.prom_name, label_key)] = (
                            counters.get((metric.prom_name, label_key), 0.0) + value
                        )
                    else:
                        timestamp = _parse_timestamp(event.get("timestamp"))
                        current = gauges.get((metric.prom_name, label_key))
                        if not current or timestamp > current[1]:
                            gauges[(metric.prom_name, label_key)] = (value, timestamp)
            except Exception:
                logger.warning(
                    "maintenance_prometheus_render_failed",
                    telemetry_path=str(event_path),
                    exc_info=True,
                )
                raise

            lines: list[str] = []
            by_prom: dict[str, _PrometheusMetric] = {m.prom_name: m for m in _PROMETHEUS_MAP.values()}
            for prom_name in sorted(by_prom.keys()):
                metric = by_prom[prom_name]
                lines.append(f"# HELP {prom_name} {metric.help}")
                lines.append(f"# TYPE {prom_name} {metric.metric_type}")
                for (name, label_key), value in sorted(counters.items()):
                    if name == prom_name:
                        lines.append(_format_prometheus_line(name, value, label_key))
                for (name, label_key), (value, _timestamp) in sorted(gauges.items()):
                    if name == prom_name:
                        lines.append(_format_prometheus_line(name, value, label_key))

            return "\n".join(lines) + ("\n" if lines else "")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_iter_events&#x22;" type="&#x22;(path) -> Iterable[dict[str, Any]]&#x22;">
      <PySourceCode>
        ```python
        def _iter_events(path: Path) -> Iterable[dict[str, Any]]:
            return iter_telemetry_events(path)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;collections.abc.Iterable[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_parse_timestamp&#x22;" type="&#x22;(value) -> datetime&#x22;">
      <PySourceCode>
        ```python
        def _parse_timestamp(value: Any) -> datetime:
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                raw = value.replace("Z", "+00:00")
                try:
                    return datetime.fromisoformat(raw)
                except ValueError:
                    pass
            return datetime.now(UTC)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;datetime.datetime&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_ensure_dict&#x22;" type="&#x22;(value) -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _ensure_dict(value: Any) -> dict[str, Any]:
            if isinstance(value, dict):
                return value
            return {}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_metric_labels&#x22;" type="&#x22;(tags) -> dict[str, str]&#x22;">
      <PySourceCode>
        ```python
        def _metric_labels(tags: dict[str, Any]) -> dict[str, str]:
            labels: dict[str, str] = {}
            for key in ("operation", "namespace", "ref", "status", "dry_run"):
                value = tags.get(key)
                if isinstance(value, str) and value:
                    labels[key] = value
            return labels
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tags&#x22;" type="&#x22;dict[str, Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_int&#x22;" type="&#x22;(value) -> int&#x22;">
      <PySourceCode>
        ```python
        def _coerce_int(value: Any) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_float&#x22;" type="&#x22;(value) -> float | None&#x22;">
      <PySourceCode>
        ```python
        def _coerce_float(value: Any) -> float | None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;float | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_bool&#x22;" type="&#x22;(value) -> bool | None&#x22;">
      <PySourceCode>
        ```python
        def _coerce_bool(value: Any) -> bool | None:
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in {"true", "1", "yes"}:
                    return True
                if value.lower() in {"false", "0", "no"}:
                    return False
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;bool | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_str&#x22;" type="&#x22;(value, fallback) -> str&#x22;">
      <PySourceCode>
        ```python
        def _coerce_str(value: Any, fallback: str) -> str:
            if isinstance(value, str) and value:
                return value
            return fallback
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />

        <PyParameter name="&#x22;fallback&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_coerce_optional_str&#x22;" type="&#x22;(value) -> str | None&#x22;">
      <PySourceCode>
        ```python
        def _coerce_optional_str(value: Any) -> str | None:
            if isinstance(value, str) and value:
                return value
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_format_prometheus_line&#x22;" type="&#x22;(name, value, labels) -> str&#x22;">
      <PySourceCode>
        ```python
        def _format_prometheus_line(name: str, value: float, labels: tuple[tuple[str, str], ...]) -> str:
            if not labels:
                return f"{name} {value}"
            label_str = ",".join(f'{key}="{val}"' for key, val in labels)
            return f"{name}{{{label_str}}} {value}"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;value&#x22;" type="&#x22;float&#x22;" value="null" />

        <PyParameter name="&#x22;labels&#x22;" type="&#x22;tuple[tuple[str, str], ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
