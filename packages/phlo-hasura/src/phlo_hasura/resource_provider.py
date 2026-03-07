"""Resource provider plugin for phlo-hasura capabilities."""

from __future__ import annotations

from phlo.capabilities import ApiBackendSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_hasura.api_backend import HasuraApiBackend


class HasuraResourceProvider(ResourceProviderPlugin):
    """Expose Hasura as a swappable API backend capability."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery."""
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="Hasura API backend capability provider",
            tags=["api", "graphql", "bi"],
        )

    def get_resources(self) -> list:
        """No raw resources are exposed in this slice."""
        return []

    def get_api_backends(self) -> list[ApiBackendSpec]:
        """Expose Hasura as an API backend capability."""
        return [
            ApiBackendSpec(
                name="hasura",
                provider=HasuraApiBackend(),
                metadata={
                    "backend_kind": "graphql",
                    "service_name": "hasura",
                    "category": "api",
                },
            )
        ]
