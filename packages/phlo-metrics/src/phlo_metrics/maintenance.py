"""Maintenance telemetry aggregation for Iceberg operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phlo.logging import get_logger
from phlo_metrics.telemetry import get_telemetry_path, iter_telemetry_events

MAINTENANCE_COMPLETE_EVENT = "iceberg.maintenance.complete"
logger = get_logger(__name__)


@dataclass(frozen=True)
class MaintenanceOperationStatus:
    """Represents the latest known status for one maintenance operation.

    Attributes:
        operation: Operation name (for example expire_snapshots).
        namespace: Catalog namespace where operation ran.
        ref: Catalog reference name.
        status: Terminal status string for the operation.
        completed_at: Completion timestamp.
        duration_seconds: Operation duration in seconds, if available.
        tables_processed: Number of tables processed.
        errors: Number of errors reported.
        snapshots_deleted: Number of snapshots removed.
        orphan_files: Number of orphan files removed or detected.
        total_records: Total records reported by maintenance telemetry.
        total_size_mb: Total size reported by maintenance telemetry in MB.
        dry_run: Whether operation ran in dry-run mode.
        run_id: Optional run identifier.
        job_name: Optional job name associated with execution.
    """

    operation: str
    namespace: str
    ref: str
    status: str
    completed_at: datetime
    duration_seconds: float | None
    tables_processed: int
    errors: int
    snapshots_deleted: int
    orphan_files: int
    total_records: int
    total_size_mb: float
    dry_run: bool | None = None
    run_id: str | None = None
    job_name: str | None = None


@dataclass(frozen=True)
class MaintenanceStatusSnapshot:
    """Represents a point-in-time view of maintenance operation statuses.

    Attributes:
        last_updated: Most recent completion timestamp in this snapshot.
        operations: Latest status entry per operation/namespace/ref tuple.
    """

    last_updated: datetime
    operations: list[MaintenanceOperationStatus]


@dataclass(frozen=True)
class _PrometheusMetric:
    """Defines Prometheus mapping metadata for a telemetry metric.

    Attributes:
        prom_name: Prometheus metric name.
        metric_type: Prometheus metric type (counter or gauge).
        help: Help text exported for the metric.
        mode: Aggregation mode for event processing.
    """

    prom_name: str
    metric_type: str
    help: str
    mode: str


_PROMETHEUS_MAP: dict[str, _PrometheusMetric] = {
    "iceberg.maintenance.run": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_runs_total",
        metric_type="counter",
        help="Total Iceberg maintenance runs",
        mode="counter",
    ),
    "iceberg.maintenance.tables_processed": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_tables_processed_total",
        metric_type="counter",
        help="Total Iceberg tables processed during maintenance",
        mode="counter",
    ),
    "iceberg.maintenance.snapshots_deleted": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_snapshots_deleted_total",
        metric_type="counter",
        help="Total Iceberg snapshots deleted during maintenance",
        mode="counter",
    ),
    "iceberg.maintenance.orphan_files": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_orphan_files_total",
        metric_type="counter",
        help="Total orphan files removed or detected during maintenance",
        mode="counter",
    ),
    "iceberg.maintenance.errors": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_errors_total",
        metric_type="counter",
        help="Total Iceberg maintenance errors",
        mode="counter",
    ),
    "iceberg.maintenance.duration_seconds": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_duration_seconds",
        metric_type="gauge",
        help="Duration of Iceberg maintenance operations in seconds",
        mode="gauge",
    ),
    "iceberg.maintenance.total_records": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_records",
        metric_type="gauge",
        help="Total records reported by Iceberg maintenance stats",
        mode="gauge",
    ),
    "iceberg.maintenance.total_size_mb": _PrometheusMetric(
        prom_name="phlo_iceberg_maintenance_size_mb",
        metric_type="gauge",
        help="Total size reported by Iceberg maintenance stats (MB)",
        mode="gauge",
    ),
}


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
            operation = _coerce_str(
                tags.get("operation") or payload.get("operation"),
                "unknown",
            )
            namespace = _coerce_str(
                tags.get("namespace") or payload.get("namespace"),
                "unknown",
            )
            ref = _coerce_str(tags.get("ref") or payload.get("ref"), "main")
            key = (operation, namespace, ref)
            status = _coerce_str(payload.get("status"), "unknown")
            entry = MaintenanceOperationStatus(
                operation=operation,
                namespace=namespace,
                ref=ref,
                status=status,
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
            "maintenance_status_load_failed",
            telemetry_path=str(event_path),
            exc_info=True,
        )
        raise

    operations = sorted(latest.values(), key=lambda item: item.completed_at, reverse=True)
    last_updated = operations[0].completed_at if operations else datetime.now(timezone.utc)
    return MaintenanceStatusSnapshot(last_updated=last_updated, operations=operations)


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
                    counters.get(
                        (metric.prom_name, label_key),
                        0.0,
                    )
                    + value
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
            if name != prom_name:
                continue
            lines.append(_format_prometheus_line(name, value, label_key))
        for (name, label_key), (value, _timestamp) in sorted(gauges.items()):
            if name != prom_name:
                continue
            lines.append(_format_prometheus_line(name, value, label_key))

    return "\n".join(lines) + ("\n" if lines else "")


def _iter_events(path: Path) -> Iterable[dict[str, Any]]:
    """Yield telemetry events from the configured telemetry file path.

    Args:
        path: Path to newline-delimited telemetry event data.

    Returns:
        Iterator of decoded telemetry event payloads.
    """
    return iter_telemetry_events(path)


def _parse_timestamp(value: Any) -> datetime:
    """Parse a timestamp into a datetime.

    Args:
        value: Timestamp value from telemetry payloads.

    Returns:
        Parsed datetime value, or current UTC time when parsing fails.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        raw = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _ensure_dict(value: Any) -> dict[str, Any]:
    """Coerce an arbitrary value to a dictionary.

    Args:
        value: Arbitrary value from telemetry payloads.

    Returns:
        The original dictionary value, or an empty dictionary.
    """
    if isinstance(value, dict):
        return value
    return {}


def _metric_labels(tags: dict[str, Any]) -> dict[str, str]:
    """Extract Prometheus label values from telemetry tags.

    Args:
        tags: Telemetry tag mapping.

    Returns:
        Filtered metric labels with non-empty string values.
    """
    labels: dict[str, str] = {}
    for key in ("operation", "namespace", "ref", "status", "dry_run"):
        value = tags.get(key)
        if isinstance(value, str) and value:
            labels[key] = value
    return labels


def _coerce_int(value: Any) -> int:
    """Coerce a value to an integer.

    Args:
        value: Input value.

    Returns:
        Parsed integer value, or ``0`` on failure.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _coerce_float(value: Any) -> float | None:
    """Coerce a value to a float.

    Args:
        value: Input value.

    Returns:
        Parsed float value, or ``None`` on failure.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    """Coerce a value to a boolean.

    Args:
        value: Input value.

    Returns:
        Parsed boolean value, or ``None`` when no bool representation exists.
    """
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


def _coerce_str(value: Any, fallback: str) -> str:
    """Coerce a value to a non-empty string with fallback.

    Args:
        value: Input value.
        fallback: Default string to return when coercion fails.

    Returns:
        Non-empty string value.
    """
    if isinstance(value, str) and value:
        return value
    return fallback


def _coerce_optional_str(value: Any) -> str | None:
    """Coerce a value to an optional non-empty string.

    Args:
        value: Input value.

    Returns:
        String value when non-empty, otherwise ``None``.
    """
    if isinstance(value, str) and value:
        return value
    return None


def _format_prometheus_line(name: str, value: float, labels: tuple[tuple[str, str], ...]) -> str:
    """Format one metric sample in Prometheus exposition format.

    Args:
        name: Prometheus metric name.
        value: Metric sample value.
        labels: Sorted key/value labels.

    Returns:
        Rendered Prometheus metric line.
    """
    if not labels:
        return f"{name} {value}"
    label_str = ",".join(f'{key}="{val}"' for key, val in labels)
    return f"{name}{{{label_str}}} {value}"
