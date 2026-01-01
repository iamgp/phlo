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
    """Scan Nessie Iceberg REST catalog for namespaces and tables."""

    def __init__(self, nessie_uri: str, timeout_seconds: int = 30):
        self.nessie_uri = nessie_uri.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_config(cls) -> NessieTableScanner:
        settings = get_settings()
        return cls(nessie_uri=settings.nessie_iceberg_rest_uri)

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
        try:
            data = self._request("GET", "/v1/namespaces")
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 404:
                logger.warning("Nessie Iceberg REST not available, falling back to Trino")
                return self._list_namespaces_via_trino()
            raise
        namespaces = data.get("namespaces", [])
        if not isinstance(namespaces, list):
            return []
        normalized: list[dict[str, Any]] = []
        for entry in namespaces:
            if isinstance(entry, dict) and "namespace" in entry:
                normalized.append(entry)
            elif isinstance(entry, list) and all(isinstance(p, str) for p in entry):
                normalized.append({"namespace": entry})
            elif isinstance(entry, str):
                normalized.append({"namespace": [entry]})
        return normalized

    def list_tables_in_namespace(self, namespace: str | list[str]) -> list[dict[str, Any]]:
        """List all tables in a namespace."""
        namespace_name = ".".join(namespace) if isinstance(namespace, list) else namespace
        try:
            data = self._request("GET", f"/v1/namespaces/{namespace_name}/tables")
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 404:
                logger.warning(
                    "Nessie Iceberg REST not available for namespace %s, using Trino",
                    namespace_name,
                )
                return self._list_tables_via_trino(namespace_name)
            raise
        tables = data.get("tables")
        if isinstance(tables, list):
            return tables
        identifiers = data.get("identifiers")
        if isinstance(identifiers, list):
            normalized_tables = []
            for ident in identifiers:
                if isinstance(ident, dict) and isinstance(ident.get("name"), str):
                    normalized_tables.append({"name": ident["name"]})
            return normalized_tables
        return []

    def get_table_metadata(self, namespace: str, table_name: str) -> dict[str, Any] | None:
        """Fetch table metadata payload from Nessie, or None if not found."""
        try:
            data = self._request("GET", f"/v1/namespaces/{namespace}/tables/{table_name}")
            return self._normalize_table_metadata(table_name, data)
        except requests.HTTPError as e:
            response = getattr(e, "response", None)
            if response is not None and response.status_code == 404:
                metadata = self._get_table_metadata_via_trino(namespace, table_name)
                if metadata:
                    return metadata
                return None
            raise

    def _list_namespaces_via_trino(self) -> list[dict[str, Any]]:
        trino = self._get_trino_resource()
        if trino is None:
            return []
        try:
            rows = trino.execute("SHOW SCHEMAS")
        except Exception as exc:  # noqa: BLE001 - log and return empty
            logger.warning("Failed to list schemas via Trino: %s", exc)
            return []
        namespaces = []
        for row in rows:
            if row and isinstance(row[0], str):
                namespaces.append({"namespace": [row[0]]})
        return namespaces

    def _list_tables_via_trino(self, namespace: str) -> list[dict[str, Any]]:
        trino = self._get_trino_resource()
        if trino is None:
            return []
        try:
            rows = trino.execute(f"SHOW TABLES FROM {namespace}")
        except Exception as exc:  # noqa: BLE001 - log and return empty
            logger.warning("Failed to list tables via Trino for %s: %s", namespace, exc)
            return []
        tables = []
        for row in rows:
            if row and isinstance(row[0], str):
                tables.append({"name": row[0]})
        return tables

    def _get_table_metadata_via_trino(
        self, namespace: str, table_name: str
    ) -> dict[str, Any] | None:
        trino = self._get_trino_resource()
        if trino is None:
            return None
        try:
            rows = trino.execute(f"DESCRIBE {namespace}.{table_name}")
        except Exception as exc:  # noqa: BLE001 - log and return None
            logger.warning(
                "Failed to describe table %s.%s via Trino: %s", namespace, table_name, exc
            )
            return None
        fields = []
        for row in rows:
            if not row:
                continue
            name = row[0] if isinstance(row[0], str) else None
            data_type = row[1] if len(row) > 1 and isinstance(row[1], str) else None
            if not name or not data_type:
                continue
            fields.append({"name": name, "type": data_type})
        if not fields:
            return None
        return {"name": table_name, "schema": {"fields": fields}}

    def _get_trino_resource(self):
        try:
            from phlo_trino import TrinoResource
        except Exception as exc:  # noqa: BLE001 - optional dependency
            logger.warning("Trino resource not available for Nessie fallback: %s", exc)
            return None
        settings = get_settings()
        return TrinoResource(
            host=settings.trino_host,
            port=settings.trino_port,
            catalog=settings.trino_catalog,
        )

    def _normalize_table_metadata(self, table_name: str, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {"name": table_name}
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return data

        normalized: dict[str, Any] = {"name": table_name}

        schema = None
        if isinstance(metadata.get("schema"), dict):
            schema = metadata.get("schema")
        else:
            schemas = metadata.get("schemas")
            current_schema_id = metadata.get("current-schema-id")
            if isinstance(schemas, list):
                if isinstance(current_schema_id, int):
                    for entry in schemas:
                        if isinstance(entry, dict) and entry.get("schema-id") == current_schema_id:
                            schema = entry
                            break
                if schema is None and schemas:
                    first = schemas[0]
                    if isinstance(first, dict):
                        schema = first
        if isinstance(schema, dict) and isinstance(schema.get("fields"), list):
            normalized["schema"] = {"fields": schema.get("fields")}

        location = metadata.get("location")
        if isinstance(location, str):
            normalized["properties"] = {"location": location}

        if isinstance(metadata.get("properties"), dict) and "properties" not in normalized:
            normalized["properties"] = metadata.get("properties")

        return normalized

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
