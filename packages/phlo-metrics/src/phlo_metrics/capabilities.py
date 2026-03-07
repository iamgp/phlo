"""Capability implementations exposed by phlo-metrics."""

from __future__ import annotations

from datetime import datetime, timezone

from phlo.capabilities.interfaces import (
    AlertSummary,
    DashboardLink,
    PlatformHealthSummary,
    PlatformMetricsSummary,
    ServiceStatus,
)

from phlo_metrics.maintenance import load_maintenance_status, render_maintenance_prometheus


class MetricsMaintenanceReadModel:
    """Expose phlo-metrics maintenance helpers as a neutral read model."""

    def load_maintenance_status(self):
        """Load the latest maintenance status snapshot."""
        return load_maintenance_status()

    def render_maintenance_prometheus(self) -> str:
        """Render maintenance metrics in Prometheus text format."""
        return render_maintenance_prometheus()


class DefaultObservabilityBackend:
    """Default observability backend composing metrics, logs, and dashboards."""

    def __init__(
        self,
        grafana_url: str | None = None,
        prometheus_url: str | None = None,
        loki_url: str | None = None,
    ):
        self._grafana_url = grafana_url or "http://grafana:3000"
        self._prometheus_url = prometheus_url or "http://prometheus:9090"
        self._loki_url = loki_url or "http://loki:3100"
        self._maintenance = MetricsMaintenanceReadModel()

    def health_summary(self) -> PlatformHealthSummary:
        """Return platform health summary."""
        try:
            maintenance = self._maintenance.load_maintenance_status()
            components = {
                "metrics": "healthy",
                "maintenance": "healthy" if maintenance.operations else "no_data",
            }
            if maintenance.operations:
                failed = any(op.status == "failed" for op in maintenance.operations)
                overall = "degraded" if failed else "healthy"
            else:
                overall = "unknown"
        except Exception:
            overall = "unhealthy"
            components = {"metrics": "unhealthy", "maintenance": "unhealthy"}

        return PlatformHealthSummary(
            overall_status=overall,
            components=components,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def service_status(self) -> list[ServiceStatus]:
        """Return service status list."""
        try:
            maintenance = self._maintenance.load_maintenance_status()
            latest_by_service: dict[str, ServiceStatus] = {}
            for operation in maintenance.operations:
                service_name = operation.job_name or operation.operation
                if service_name in latest_by_service:
                    continue
                status = "healthy" if operation.status == "completed" else "unknown"
                latest_by_service[service_name] = ServiceStatus(
                    name=service_name,
                    status=status,
                    last_check=operation.completed_at.isoformat(),
                )
            return [latest_by_service[name] for name in sorted(latest_by_service)]
        except Exception:
            return [
                ServiceStatus(
                    name="metrics",
                    status="unknown",
                    last_check=datetime.now(timezone.utc).isoformat(),
                )
            ]

    def platform_metrics(self, period: str) -> PlatformMetricsSummary:
        """Return platform metrics for the specified period."""
        try:
            maintenance = self._maintenance.load_maintenance_status()
            total_ops = len(maintenance.operations)
            failed_ops = sum(1 for op in maintenance.operations if op.status == "failed")
            metrics = {
                "total_maintenance_operations": total_ops,
                "failed_operations": failed_ops,
                "successful_operations": total_ops - failed_ops,
            }
        except Exception:
            metrics = {"error": "failed_to_load_metrics"}

        return PlatformMetricsSummary(
            period=period,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def recent_alerts(self, limit: int) -> list[AlertSummary]:
        """Return recent alerts up to the specified limit."""
        try:
            maintenance = self._maintenance.load_maintenance_status()
            failed_ops = [op for op in maintenance.operations if op.status == "failed"]
            alerts = []
            for op in failed_ops[:limit]:
                alerts.append(
                    AlertSummary(
                        title=f"Maintenance operation {op.operation} failed",
                        severity="error",
                        status="firing",
                        fired_at=op.completed_at.isoformat(),
                    )
                )
            return alerts
        except Exception:
            return []

    def dashboard_links(self) -> list[DashboardLink]:
        """Return available dashboard links."""
        return [
            DashboardLink(
                title="Platform Overview",
                url=f"{self._grafana_url}/d/platform-overview",
                category="overview",
            ),
            DashboardLink(
                title="Maintenance Operations",
                url=f"{self._grafana_url}/d/maintenance-operations",
                category="maintenance",
            ),
        ]

    def logs_query_link(self, service: str | None = None) -> str | None:
        """Return a link to query logs."""
        if service:
            return f"{self._loki_url}/logs?service={service}"
        return f"{self._loki_url}/logs"

    def metrics_query_link(self, metric: str | None = None) -> str | None:
        """Return a link to query metrics."""
        if metric:
            return f"{self._prometheus_url}/graph?g0.expr={metric}"
        return f"{self._prometheus_url}/graph"
