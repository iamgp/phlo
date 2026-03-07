"""Tests for phlo-alerting resource provider."""

from __future__ import annotations

from phlo_alerting.resource_provider import AlertingResourceProvider


def test_alerting_resource_provider_exposes_alert_sink() -> None:
    """Alerting package should register a neutral alert sink."""
    provider = AlertingResourceProvider()

    specs = provider.get_alert_sinks()

    assert [spec.name for spec in specs] == ["alerting"]
    assert hasattr(specs[0].provider, "send_alert")
