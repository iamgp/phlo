"""Tests for phlo-metrics resource provider."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from phlo_metrics.capabilities import DefaultObservabilityBackend
from phlo_metrics.resource_provider import MetricsResourceProvider


class _Operation:
    def __init__(self, operation: str, status: str, completed_at: datetime, job_name: str | None):
        self.operation = operation
        self.status = status
        self.completed_at = completed_at
        self.job_name = job_name


class _Snapshot:
    def __init__(self, operations: list[_Operation]):
        self.operations = operations


def test_metrics_resource_provider_exposes_maintenance_read_model() -> None:
    """Metrics package should register a neutral maintenance read model."""
    provider = MetricsResourceProvider()

    specs = provider.get_maintenance_read_models()

    assert [spec.name for spec in specs] == ["metrics"]
    assert hasattr(specs[0].provider, "load_maintenance_status")
    assert hasattr(specs[0].provider, "render_maintenance_prometheus")


def test_metrics_resource_provider_exposes_observability_backend() -> None:
    """Metrics package should register a default observability backend."""
    provider = MetricsResourceProvider()

    specs = provider.get_observability_backends()

    assert [spec.name for spec in specs] == ["default"]
    assert isinstance(specs[0].provider, DefaultObservabilityBackend)
    assert specs[0].support.supports_metrics is True
    assert specs[0].support.supports_logs is True
    assert specs[0].support.supports_dashboards is True
    assert specs[0].support.supports_alerts is True


def test_default_observability_backend_has_required_methods() -> None:
    """Default observability backend should implement the ObservabilityBackend protocol."""
    backend = DefaultObservabilityBackend()

    assert hasattr(backend, "health_summary")
    assert hasattr(backend, "service_status")
    assert hasattr(backend, "platform_metrics")
    assert hasattr(backend, "recent_alerts")
    assert hasattr(backend, "dashboard_links")
    assert hasattr(backend, "logs_query_link")
    assert hasattr(backend, "metrics_query_link")


def test_default_observability_backend_returns_expected_types() -> None:
    """Default observability backend methods should return expected types."""
    backend = DefaultObservabilityBackend()

    health = backend.health_summary()
    assert hasattr(health, "overall_status")
    assert hasattr(health, "components")
    assert hasattr(health, "timestamp")

    services = backend.service_status()
    assert isinstance(services, list)

    metrics = backend.platform_metrics("24h")
    assert hasattr(metrics, "period")
    assert hasattr(metrics, "metrics")
    assert hasattr(metrics, "timestamp")

    alerts = backend.recent_alerts(10)
    assert isinstance(alerts, list)

    links = backend.dashboard_links()
    assert isinstance(links, list)

    logs_link = backend.logs_query_link("test-service")
    assert isinstance(logs_link, str) or logs_link is None

    metrics_link = backend.metrics_query_link("test_metric")
    assert isinstance(metrics_link, str) or metrics_link is None


def test_recent_alerts_limits_after_filtering_failures(monkeypatch) -> None:
    """Alert limit should apply after selecting failed operations."""
    now = datetime.now(timezone.utc)
    backend = DefaultObservabilityBackend()
    snapshot = _Snapshot(
        operations=[
            _Operation("compact", "completed", now, "dagster"),
            _Operation("expire", "completed", now - timedelta(minutes=1), "dagster"),
            _Operation("cleanup", "failed", now - timedelta(minutes=2), "dagster"),
            _Operation("vacuum", "failed", now - timedelta(minutes=3), "dagster"),
        ]
    )
    monkeypatch.setattr(backend._maintenance, "load_maintenance_status", lambda: snapshot)

    alerts = backend.recent_alerts(1)

    assert len(alerts) == 1
    assert alerts[0].title == "Maintenance operation cleanup failed"


def test_service_status_is_sorted_deterministically(monkeypatch) -> None:
    """Service list should not depend on set iteration order."""
    now = datetime.now(timezone.utc)
    backend = DefaultObservabilityBackend()
    snapshot = _Snapshot(
        operations=[
            _Operation("compact", "completed", now, "zeta"),
            _Operation("expire", "completed", now - timedelta(minutes=1), "alpha"),
            _Operation("vacuum", "completed", now - timedelta(minutes=2), "alpha"),
        ]
    )
    monkeypatch.setattr(backend._maintenance, "load_maintenance_status", lambda: snapshot)

    services = backend.service_status()

    assert [service.name for service in services] == ["alpha", "zeta"]


def test_links_resolve_from_service_config(monkeypatch, tmp_path: Path) -> None:
    """Service config should drive generated observability links."""
    backend = DefaultObservabilityBackend()
    grafana_dir = tmp_path / "grafana"
    dashboards_dir = grafana_dir / "dashboards"
    dashboards_dir.mkdir(parents=True)
    (dashboards_dir / "overview.json").write_text(
        '{"uid": "phlo-overview", "title": "Phlo Lakehouse - Overview"}',
        encoding="utf-8",
    )

    services = {
        "grafana": SimpleNamespace(
            env_vars={
                "GRAFANA_PORT": {"default": 3003},
                "GRAFANA_DASHBOARD_PATH_TEMPLATE": {"default": "/d/{uid}"},
            },
            source_path=grafana_dir,
        ),
        "loki": SimpleNamespace(
            env_vars={
                "LOKI_PORT": {"default": 3100},
                "LOKI_LOGS_PATH": {"default": "/logs"},
            },
        ),
        "prometheus": SimpleNamespace(
            env_vars={
                "PROMETHEUS_PORT": {"default": 9090},
                "PROMETHEUS_QUERY_PATH": {"default": "/graph"},
            },
        ),
    }

    class _StubDiscovery:
        def get_service(self, name: str):
            return services.get(name)

    monkeypatch.setattr("phlo_metrics.capabilities.ServiceDiscovery", lambda: _StubDiscovery())

    links = backend.dashboard_links()

    assert links[0].url == "http://localhost:3003/d/phlo-overview"
    assert backend.logs_query_link("dagster") == "http://localhost:3100/logs?service=dagster"
    assert backend.metrics_query_link("up") == "http://localhost:9090/graph?g0.expr=up"
