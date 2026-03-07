"""Capability wrapper for Hasura as an API backend."""

from __future__ import annotations

from typing import Any

import requests

from phlo_hasura.client import HasuraClient


class HasuraApiBackend:
    """Expose Hasura through the neutral API backend capability."""

    def __init__(self, client: HasuraClient | None = None) -> None:
        self._client = client or HasuraClient()

    def health_check(self) -> bool:
        """Check whether the Hasura health endpoint responds successfully."""
        try:
            response = requests.get(f"{self._client.hasura_url}/healthz", timeout=5)
        except requests.RequestException:
            return False
        return response.status_code in {200, 204}

    def describe(self) -> dict[str, Any]:
        """Return a stable description of the Hasura backend surface."""
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
