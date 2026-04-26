"""Resource provider for ClickStack observability capabilities."""

from __future__ import annotations

from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_clickstack.observability_backend import build_clickstack_observability_spec


class ClickStackResourceProvider(ResourceProviderPlugin):
    """Expose ClickStack as the default observability backend capability."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="ClickStack observability capability provider",
            tags=["observability", "logs", "metrics", "traces"],
        )

    def get_resources(self) -> list:
        return []

    def get_observability_backends(self):
        return [build_clickstack_observability_spec()]
