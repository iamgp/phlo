"""Hook plugin for capturing telemetry events."""

from __future__ import annotations

from typing import Any

from phlo.hooks import TelemetryEvent
from phlo.plugins.base import PluginMetadata
from phlo.plugins.hooks import HookFilter, HookPlugin, HookRegistration

from phlo_metrics.telemetry import TelemetryRecorder


class MetricsHookPlugin(HookPlugin):
    def __init__(self) -> None:
        self._recorder = TelemetryRecorder()

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics",
            version="0.1.0",
            description="Telemetry hooks for metrics capture",
        )

    def get_hooks(self) -> list[HookRegistration]:
        return [
            HookRegistration(
                hook_name="metrics_telemetry",
                handler=self._handle_telemetry,
                filters=HookFilter(event_types={"telemetry.log", "telemetry.metric"}),
            )
        ]

    def _handle_telemetry(self, event: Any) -> None:
        if not isinstance(event, TelemetryEvent):
            return
        self._recorder.record(event)
