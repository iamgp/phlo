"""Resource provider plugin for phlo-lineage capabilities."""

from __future__ import annotations

from phlo.capabilities import LineageSinkSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_lineage.lineage_sink import PhloLineageSink


class LineageResourceProvider(ResourceProviderPlugin):
    """Expose phlo-lineage as a lineage sink capability."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery."""
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Lineage sink capability provider",
            tags=["lineage"],
        )

    def get_resources(self) -> list:
        """No raw resources are exposed in this slice."""
        return []

    def get_lineage_sinks(self) -> list[LineageSinkSpec]:
        """Expose the phlo-lineage sink capability."""
        return [
            LineageSinkSpec(
                name="phlo-lineage",
                provider=PhloLineageSink(),
            )
        ]
