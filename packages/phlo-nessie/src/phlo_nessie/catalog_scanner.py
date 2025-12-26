"""
Nessie catalog scanner for table discovery.

This module provides a lightweight Nessie API client focused on catalog discovery:
- namespaces (schemas)
- tables within namespaces
- per-table metadata payloads

It deliberately does not know about any downstream metadata systems (e.g., OpenMetadata).
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from phlo.config import get_settings

logger = logging.getLogger(__name__)


class NessieTableScanner:
    """Scan Nessie for namespaces/tables via the Nessie REST API v1."""

    def __init__(self, nessie_uri: str, timeout_seconds: int = 30):
        self.nessie_uri = nessie_uri.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_config(cls) -> NessieTableScanner:
        settings = get_settings()
        return cls(nessie_uri=settings.nessie_api_v1_uri)

    def _request(self, method: str, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.nessie_uri.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json() if response.text else {}

    def list_namespaces(self) -> list[dict[str, Any]]:
        """List namespaces from Nessie."""
        data = self._request("GET", "/namespaces")
        namespaces = data.get("namespaces", [])
        if not isinstance(namespaces, list):
            return []
        return namespaces

    def list_tables_in_namespace(self, namespace: str | list[str]) -> list[dict[str, Any]]:
        """List all tables in a namespace."""
        namespace_name = ".".join(namespace) if isinstance(namespace, list) else namespace
        data = self._request("GET", f"/namespaces/{namespace_name}/tables")
        tables = data.get("tables", [])
        if not isinstance(tables, list):
            return []
        return tables

    def get_table_metadata(self, namespace: str, table_name: str) -> dict[str, Any] | None:
        """Fetch table metadata payload from Nessie, or None if not found."""
        try:
            return self._request("GET", f"/namespaces/{namespace}/tables/{table_name}")
        except requests.HTTPError as e:
            response = getattr(e, "response", None)
            if response is not None and response.status_code == 404:
                return None
            raise

    def scan_all_tables(self) -> dict[str, list[dict[str, Any]]]:
        """Return mapping of namespace -> tables list (as returned by Nessie)."""
        catalog: dict[str, list[dict[str, Any]]] = {}
        for ns_obj in self.list_namespaces():
            ns_parts = ns_obj.get("namespace")
            if not isinstance(ns_parts, list) or not all(isinstance(p, str) for p in ns_parts):
                continue
            ns_name = ".".join(ns_parts)
            catalog[ns_name] = self.list_tables_in_namespace(ns_parts)
        return catalog
