"""Metrics collection and exposure for Phlo pipeline."""

from __future__ import annotations

from typing import Any

__all__ = [
    "MetricsCollector",
    "get_metrics_collector",
    "SummaryMetrics",
    "AssetMetrics",
    "RunMetrics",
    "TelemetryRecorder",
    "MaintenanceOperationStatus",
    "MaintenanceStatusSnapshot",
    "load_maintenance_status",
    "render_maintenance_prometheus",
    "get_telemetry_path",
    "iter_telemetry_events",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve package exports to avoid import cycles during plugin discovery."""
    if name in {
        "AssetMetrics",
        "MetricsCollector",
        "RunMetrics",
        "SummaryMetrics",
        "get_metrics_collector",
    }:
        from phlo_metrics import collector as collector_module

        return getattr(collector_module, name)
    if name in {
        "MaintenanceOperationStatus",
        "MaintenanceStatusSnapshot",
        "load_maintenance_status",
        "render_maintenance_prometheus",
    }:
        from phlo_metrics import maintenance as maintenance_module

        return getattr(maintenance_module, name)
    if name in {
        "TelemetryRecorder",
        "get_telemetry_path",
        "iter_telemetry_events",
    }:
        from phlo_metrics import telemetry as telemetry_module

        return getattr(telemetry_module, name)
    raise AttributeError(name)
