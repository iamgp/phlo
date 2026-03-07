"""Resource provider plugin for phlo-metrics capabilities."""

from __future__ import annotations

from phlo.capabilities import MaintenanceReadModelSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_metrics.maintenance import load_maintenance_status, render_maintenance_prometheus


class MetricsMaintenanceReadModel:
    """Expose phlo-metrics maintenance helpers as a neutral read model."""

    def load_maintenance_status(self):
        """Load the latest maintenance status snapshot."""
        return load_maintenance_status()

    def render_maintenance_prometheus(self) -> str:
        """Render maintenance metrics in Prometheus text format."""
        return render_maintenance_prometheus()


class MetricsResourceProvider(ResourceProviderPlugin):
    """Expose phlo-metrics capabilities for runtime discovery."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery."""
        return PluginMetadata(
            name="metrics",
            version="0.1.0",
            description="Metrics capability provider",
            tags=["metrics", "maintenance"],
        )

    def get_resources(self) -> list:
        """No raw resources are exposed in this slice."""
        return []

    def get_maintenance_read_models(self) -> list[MaintenanceReadModelSpec]:
        """Expose phlo-metrics as a maintenance read-model capability."""
        return [
            MaintenanceReadModelSpec(
                name="metrics",
                provider=MetricsMaintenanceReadModel(),
            )
        ]
