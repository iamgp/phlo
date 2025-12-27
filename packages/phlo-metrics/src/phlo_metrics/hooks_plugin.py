"""Hook plugin for capturing telemetry events."""

from __future__ import annotations

from typing import Any

from phlo.hooks import TelemetryEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_metrics.telemetry import TelemetryRecorder


class MetricsHookPlugin(HookPlugin):
    """Capture telemetry events into the metrics recorder."""

    def __init__(self) -> None:
        """Initialize the telemetry recorder."""

        self._recorder = TelemetryRecorder()

    @property
    def metadata(self) -> PluginMetadata:
        """Metadata for the metrics hook plugin."""

        return PluginMetadata(
            name="metrics",
            version="0.1.0",
            description="Telemetry hooks for metrics capture",
        )

    def get_hooks(self) -> list[HookRegistration]:
        """Register telemetry hook handlers."""

        return [
            HookRegistration(
                hook_name="metrics_telemetry",
                handler=self._handle_telemetry,
                filters=HookFilter(event_types={"telemetry.log", "telemetry.metric"}),
            )
        ]

    def _handle_telemetry(self, event: Any) -> None:
        """Record telemetry events from the hook bus."""

        if not isinstance(event, TelemetryEvent):
            return
        self._recorder.record(event)
