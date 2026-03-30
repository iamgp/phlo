"""Resource provider plugin for phlo-hasura capabilities.

This module provides the HasuraResourceProvider class that exposes Hasura
as an API backend capability through the Phlo resource provider system.

The provider allows Hasura to be discovered and used as a swappable
GraphQL API backend by other components in the Phlo ecosystem.

Example:
    >>> from phlo_hasura.resource_provider import HasuraResourceProvider
    >>> provider = HasuraResourceProvider()
    >>> backends = provider.get_api_backends()
    >>> print(backends[0].name)
    'hasura'

"""

from __future__ import annotations

from phlo.capabilities import ApiBackendSpec
from phlo.plugins import PluginMetadata, ResourceProviderPlugin

from phlo_hasura.api_backend import HasuraApiBackend


class HasuraResourceProvider(ResourceProviderPlugin):
    """Expose Hasura as a swappable API backend capability.

    This provider integrates Hasura with the Phlo capability system,
    allowing it to be discovered and used as a GraphQL API backend.

    Attributes:
        _metadata: Cached plugin metadata.

    Example:
        >>> provider = HasuraResourceProvider()
        >>> provider.metadata.name
        'hasura'
        >>> backends = provider.get_api_backends()
        >>> backends[0].metadata['backend_kind']
        'graphql'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for capability discovery.

        Returns:
            PluginMetadata containing:
                - name: Provider identifier ('hasura')
                - version: Provider version
                - description: Brief description
                - tags: Capability tags for filtering

        Example:
            >>> provider = HasuraResourceProvider()
            >>> meta = provider.metadata
            >>> print(meta.name, meta.tags)
            hasura ['api', 'graphql', 'bi']

        """
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="Hasura API backend capability provider",
            tags=["api", "graphql", "bi"],
        )

    def get_resources(self) -> list:
        """Return list of raw resources exposed by this provider.

        This provider does not expose any raw resources directly.
        Resources are accessed through the API backend interface.

        Returns:
            Empty list as no raw resources are provided.

        """
        return []

    def get_api_backends(self) -> list[ApiBackendSpec]:
        """Expose Hasura as an API backend capability.

        Returns Hasura API backend specifications that can be used
        by other components requiring a GraphQL API backend.

        Returns:
            List containing the Hasura API backend specification with
            name, provider instance, and metadata.

        Example:
            >>> provider = HasuraResourceProvider()
            >>> backends = provider.get_api_backends()
            >>> backends[0].name
            'hasura'
            >>> backends[0].metadata['backend_kind']
            'graphql'

        """
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
