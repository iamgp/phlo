"""Tests for Dagster alerting sensor utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from phlo_dagster import alerting_sensor


class _TestSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class _TestAlert:
    title: str
    message: str
    severity: _TestSeverity
    asset_name: str | None = None
    run_id: str | None = None
    error_message: str | None = None
    timestamp: datetime | None = None


class _Manager:
    def __init__(self) -> None:
        self.last_alert: _TestAlert | None = None

    def send(self, alert: _TestAlert) -> bool:
        # Mirrors alert manager behavior that requires enum severity.
        _ = alert.severity.value
        self.last_alert = alert
        return True


def test_send_alert_coerces_none_severity_to_error(monkeypatch) -> None:
    """Non-string severities should safely default to ERROR."""
    manager = _Manager()
    monkeypatch.setattr(
        alerting_sensor,
        "_load_alerting",
        lambda: (_TestAlert, _TestSeverity, lambda: manager),
    )

    result = alerting_sensor.send_alert(title="A", message="B", severity=None)

    assert result is True
    assert manager.last_alert is not None
    assert manager.last_alert.severity == _TestSeverity.ERROR


def test_send_alert_coerces_invalid_string_to_error(monkeypatch) -> None:
    """Invalid string severities should safely default to ERROR."""
    manager = _Manager()
    monkeypatch.setattr(
        alerting_sensor,
        "_load_alerting",
        lambda: (_TestAlert, _TestSeverity, lambda: manager),
    )

    result = alerting_sensor.send_alert(title="A", message="B", severity="not-valid")

    assert result is True
    assert manager.last_alert is not None
    assert manager.last_alert.severity == _TestSeverity.ERROR
