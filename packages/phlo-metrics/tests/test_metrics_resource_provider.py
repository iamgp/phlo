"""Tests for phlo-metrics resource provider."""

from __future__ import annotations

from phlo_metrics.resource_provider import MetricsResourceProvider


def test_metrics_resource_provider_exposes_maintenance_read_model() -> None:
    """Metrics package should register a neutral maintenance read model."""
    provider = MetricsResourceProvider()

    specs = provider.get_maintenance_read_models()

    assert [spec.name for spec in specs] == ["metrics"]
    assert hasattr(specs[0].provider, "load_maintenance_status")
    assert hasattr(specs[0].provider, "render_maintenance_prometheus")
