"""Capability wrapper for Hasura as an API backend.

This module provides the HasuraApiBackend class that exposes Hasura's
GraphQL capabilities through a neutral API backend interface.

The backend handles health checks and provides metadata describing
the Hasura GraphQL endpoints available to consumers.

Example:
    >>> from phlo_hasura.api_backend import HasuraApiBackend
    >>> backend = HasuraApiBackend()
    >>> backend.health_check()
    True
    >>> backend.describe()
    {"service_name": "hasura", "backend_kind": "graphql", ...}

"""

from __future__ import annotations

from typing import Any

import requests

from phlo_hasura.client import HasuraClient


class HasuraApiBackend:
    """Expose Hasura through the neutral API backend capability.

    This class wraps the Hasura GraphQL engine to provide a standardized
    API backend interface. It handles health checks and returns metadata
    describing the available endpoints.

    Attributes:
        _client: The internal HasuraClient instance for making API calls.

    Example:
        >>> backend = HasuraApiBackend()
        >>> if backend.health_check():
        ...     print("Hasura is healthy")
        ...     config = backend.describe()
        ...     print(f"GraphQL endpoint: {config['default_path']}")

    """

    def __init__(self, client: HasuraClient | None = None) -> None:
        """Initialize the Hasura API backend.

        Args:
            client: HasuraClient instance. If not provided, a new
                HasuraClient will be instantiated with default settings.

        Example:
            >>> backend = HasuraApiBackend()
            >>> custom_backend = HasuraApiBackend(HasuraClient(
            ...     hasura_url="http://custom:8080"
            ... ))

        """
        self._client = client or HasuraClient()

    def health_check(self) -> bool:
        """Check whether the Hasura health endpoint responds successfully.

        Makes a GET request to the /healthz endpoint to verify that
        Hasura is running and responsive.

        Returns:
            True if the health endpoint returns 200 or 204, False otherwise.

        Raises:
            No exceptions are raised; all errors are caught and return False.

        Example:
            >>> backend = HasuraApiBackend()
            >>> if backend.health_check():
            ...     print("Hasura is up and running")
            ... else:
            ...     print("Hasura is not responding")

        """
        try:
            response = requests.get(f"{self._client.hasura_url}/healthz", timeout=5)
        except requests.RequestException:
            return False
        return response.status_code in {200, 204}

    def describe(self) -> dict[str, Any]:
        """Return a stable description of the Hasura backend surface.

        Returns metadata describing the Hasura GraphQL API endpoints,
        including the base URL, health check path, and available
        public endpoints.

        Returns:
            Dictionary containing:
                - service_name: The service identifier ("hasura")
                - backend_kind: The type of backend ("graphql")
                - default_path: Default GraphQL endpoint path
                - health_path: Health check endpoint path
                - metadata_path: Metadata API endpoint path
                - base_url: Base URL for all endpoints
                - public_endpoints: List of available endpoints with names and URLs

        Example:
            >>> backend = HasuraApiBackend()
            >>> desc = backend.describe()
            >>> print(desc["service_name"])
            "hasura"
            >>> for ep in desc["public_endpoints"]:
            ...     print(f"{ep['name']}: {ep['url']}")

        """
        base_url = self._client.hasura_url.rstrip("/")
        return {
            "service_name": "hasura",
            "backend_kind": "graphql",
            "default_path": "/v1/graphql",
            "health_path": "/healthz",
            "metadata_path": "/v1/metadata",
            "base_url": base_url,
            "public_endpoints": [
                {"name": "graphql", "url": f"{base_url}/v1/graphql"},
                {"name": "metadata", "url": f"{base_url}/v1/metadata"},
                {"name": "health", "url": f"{base_url}/healthz"},
            ],
        }
