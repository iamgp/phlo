"""Resource provider plugin for phlo-metrics capabilities."""

from __future__ import annotations

from phlo.capabilities import CapabilitySupport, MaintenanceReadModelSpec, ObservabilityBackendSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_metrics.capabilities import DefaultObservabilityBackend, MetricsMaintenanceReadModel


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

    def get_observability_backends(self) -> list[ObservabilityBackendSpec]:
        """Expose phlo-metrics as an observability backend capability."""
        return [
            ObservabilityBackendSpec(
                name="default",
                provider=DefaultObservabilityBackend(),
                metadata={
                    "default_stack": [
                        "phlo-metrics",
                        "phlo-otel",
                        "phlo-clickstack",
                    ],
                    "service_dependencies": ["clickstack"],
                },
                support=CapabilitySupport(
                    supports_metrics=True,
                    supports_logs=True,
                    supports_dashboards=True,
                    supports_alerts=True,
                ),
            )
        ]
