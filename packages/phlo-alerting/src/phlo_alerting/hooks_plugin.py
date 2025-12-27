"""Hook plugin for alerting on quality and telemetry events."""

from __future__ import annotations

from typing import Any

from phlo.hooks import QualityResultEvent, TelemetryEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_alerting.manager import Alert, AlertSeverity, get_alert_manager


class AlertingHookPlugin(HookPlugin):
    """Emit alerts based on quality and telemetry events."""

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata for the alerting hook plugin."""

        return PluginMetadata(
            name="alerting",
            version="0.1.0",
            description="Alerting hooks for quality and telemetry events",
        )

    def get_hooks(self) -> list[HookRegistration]:
        """Register quality and telemetry hook handlers."""

        return [
            HookRegistration(
                hook_name="alerting_quality",
                handler=self._handle_quality,
                filters=HookFilter(event_types={"quality.result"}),
            ),
            HookRegistration(
                hook_name="alerting_telemetry",
                handler=self._handle_telemetry,
                filters=HookFilter(event_types={"telemetry.log", "telemetry.metric"}),
            ),
        ]

    def _handle_quality(self, event: Any) -> None:
        """Send an alert for failed quality checks."""

        if not isinstance(event, QualityResultEvent):
            return
        if event.passed:
            return
        severity = _map_quality_severity(event.severity)
        message = _format_quality_message(event)
        alert = Alert(
            title=f"Quality check failed: {event.check_name}",
            message=message,
            severity=severity,
            asset_name=event.asset_key,
        )
        get_alert_manager().send(alert)

    def _handle_telemetry(self, event: Any) -> None:
        """Send an alert for error-level telemetry events."""

        if not isinstance(event, TelemetryEvent):
            return
        if not event.level or event.level.lower() not in {"error", "critical"}:
            return
        alert = Alert(
            title=f"Telemetry {event.level} event: {event.name}",
            message=str(event.payload or event.value or ""),
            severity=_map_telemetry_severity(event.level),
            asset_name=event.tags.get("asset"),
        )
        get_alert_manager().send(alert)


def _map_quality_severity(severity: str | None) -> AlertSeverity:
    """Map quality severity strings to alert severities."""

    if not severity:
        return AlertSeverity.ERROR
    value = severity.upper()
    if value == "WARN":
        return AlertSeverity.WARNING
    if value in {"CRITICAL", "FATAL"}:
        return AlertSeverity.CRITICAL
    return AlertSeverity.ERROR


def _map_telemetry_severity(level: str) -> AlertSeverity:
    """Map telemetry levels to alert severities."""

    value = level.lower()
    if value == "critical":
        return AlertSeverity.CRITICAL
    return AlertSeverity.ERROR


def _format_quality_message(event: QualityResultEvent) -> str:
    """Format a human-readable quality failure message."""

    parts = [
        f"Asset: {event.asset_key}",
        f"Check: {event.check_name}",
    ]
    if event.partition_key:
        parts.append(f"Partition: {event.partition_key}")
    if event.metadata.get("error"):
        parts.append(f"Error: {event.metadata['error']}")
    if event.metadata.get("failure_message"):
        parts.append(f"Details: {event.metadata['failure_message']}")
    return "\n".join(parts)
