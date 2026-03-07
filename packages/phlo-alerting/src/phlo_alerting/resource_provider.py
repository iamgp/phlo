"""Resource provider plugin for phlo-alerting capabilities."""

from __future__ import annotations

from phlo.capabilities import AlertSinkSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_alerting.alert_sink import AlertManagerSink


class AlertingResourceProvider(ResourceProviderPlugin):
    """Expose phlo-alerting as a neutral alert sink capability."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery."""
        return PluginMetadata(
            name="alerting",
            version="0.1.0",
            description="Alert sink capability provider",
            tags=["alerting"],
        )

    def get_resources(self) -> list:
        """No raw resources are exposed in this slice."""
        return []

    def get_alert_sinks(self) -> list[AlertSinkSpec]:
        """Expose phlo-alerting as an alert sink capability."""
        return [
            AlertSinkSpec(
                name="alerting",
                provider=AlertManagerSink(),
            )
        ]
