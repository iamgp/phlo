"""
Nessie catalog scanner for Iceberg table metadata extraction.

Scans the Nessie Git-like catalog and extracts table schemas,
partitioning info, and properties for syncing to OpenMetadata.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import requests

from phlo.catalog.openmetadata import OpenMetadataColumn, OpenMetadataTable
from phlo.config import get_settings

logger = logging.getLogger(__name__)


class NessieTableScanner:
    """
    Scans Nessie catalog for Iceberg tables and extracts metadata.

    Discovers all tables in the Nessie catalog and extracts their schemas,
    column information, and partitioning details for syncing to OpenMetadata.
    """

    def __init__(
        self,
        nessie_uri: str,
        timeout: int = 30,
    ):
        """
        Initialize Nessie scanner.

        Args:
            nessie_uri: Base URI of Nessie API (e.g., http://nessie:19120/api/v1)
            timeout: Request timeout in seconds
        """
        self.nessie_uri = nessie_uri.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_config(cls) -> NessieTableScanner:
        """Create scanner from application config."""
        config = get_settings()
        return cls(nessie_uri=config.nessie_api_v1_uri)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make request to Nessie API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON
        """
        url = urljoin(self.nessie_uri, endpoint)

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Nessie request failed: {method} {endpoint}: {e}")
            raise

    def list_namespaces(self) -> list[dict[str, Any]]:
        """
        List all namespaces (schemas) in the catalog.

        Returns:
            List of namespace objects
        """
        try:
            response = self._request("GET", "/namespaces")
            return response.get("namespaces", [])
        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []

    def list_tables_in_namespace(self, namespace: str | list[str]) -> list[dict[str, Any]]:
        """
        List all tables in a namespace.

        Args:
            namespace: Namespace name or list of namespace parts

        Returns:
            List of table objects
        """
        if isinstance(namespace, list):
            namespace = ".".join(namespace)

        try:
            response = self._request(
                "GET",
                f"/namespaces/{namespace}/tables",
            )
            return response.get("tables", [])
        except Exception as e:
            logger.error(f"Failed to list tables in {namespace}: {e}")
            return []

    def get_table_metadata(self, namespace: str, table_name: str) -> Optional[dict[str, Any]]:
        """
        Get detailed metadata for a specific table.

        Args:
            namespace: Namespace name
            table_name: Table name

        Returns:
            Table metadata or None if not found
        """
        try:
            response = self._request(
                "GET",
                f"/namespaces/{namespace}/tables/{table_name}",
            )
            return response
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"Table not found: {namespace}.{table_name}")
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get metadata for {namespace}.{table_name}: {e}")
            return None

    def scan_all_tables(self) -> dict[str, list[dict[str, Any]]]:
        """
        Scan entire catalog and collect all tables by namespace.

        Returns:
            Dictionary mapping namespace names to lists of table metadata
        """
        catalog = {}

        try:
            namespaces = self.list_namespaces()
            logger.info(f"Found {len(namespaces)} namespaces in Nessie")

            for ns_obj in namespaces:
                ns_name = ".".join(ns_obj["namespace"])
                logger.info(f"Scanning namespace: {ns_name}")

                tables = self.list_tables_in_namespace(ns_obj["namespace"])
                logger.info(f"  Found {len(tables)} tables")

                catalog[ns_name] = tables

        except Exception as e:
            logger.error(f"Error scanning catalog: {e}")

        return catalog

    def extract_openmetadata_table(
        self,
        namespace: str,
        table_metadata: dict[str, Any],
        description: Optional[str] = None,
    ) -> OpenMetadataTable:
        """
        Convert Nessie table metadata to OpenMetadata format.

        Args:
            namespace: Namespace name
            table_metadata: Table metadata from Nessie
            description: Optional table description

        Returns:
            OpenMetadataTable object
        """
        table_name = table_metadata.get("name", "unknown")
        schema = table_metadata.get("schema", {})

        # Extract columns from Iceberg schema
        columns = []
        field_id = 0

        for field in schema.get("fields", []):
            col_type = self._map_iceberg_to_om_type(field.get("type", "unknown"))

            column = OpenMetadataColumn(
                name=field.get("name", f"col_{field_id}"),
                dataType=col_type,
                description=field.get("doc"),
                ordinalPosition=field_id,
            )
            columns.append(column)
            field_id += 1

        # Extract table properties
        location = None
        if "properties" in table_metadata:
            location = table_metadata["properties"].get("location")

        table = OpenMetadataTable(
            name=table_name,
            description=description or table_metadata.get("doc"),
            columns=columns if columns else None,
            tableType="Regular",
            location=location,
        )

        return table

    @staticmethod
    def _map_iceberg_to_om_type(iceberg_type: str) -> str:
        """
        Map Iceberg type to OpenMetadata type.

        Args:
            iceberg_type: Iceberg type string

        Returns:
            OpenMetadata type string
        """
        type_map = {
            "boolean": "BOOLEAN",
            "int": "INT",
            "long": "LONG",
            "float": "FLOAT",
            "double": "DOUBLE",
            "decimal": "DECIMAL",
            "date": "DATE",
            "time": "TIME",
            "timestamp": "TIMESTAMP",
            "timestamptz": "TIMESTAMPTZ",
            "string": "STRING",
            "uuid": "UUID",
            "fixed": "FIXED",
            "binary": "BINARY",
            "struct": "STRUCT",
            "list": "ARRAY",
            "map": "MAP",
        }

        # Handle complex types like list<int>, struct<...>, etc.
        base_type = iceberg_type.split("<")[0].lower()
        return type_map.get(base_type, "UNKNOWN")

    def sync_to_openmetadata(
        self,
        om_client: Any,  # OpenMetadataClient
        include_namespaces: Optional[list[str]] = None,
        exclude_namespaces: Optional[list[str]] = None,
    ) -> dict[str, int]:
        """
        Sync all Nessie tables to OpenMetadata.

        Args:
            om_client: OpenMetadataClient instance
            include_namespaces: Only sync these namespaces (if set)
            exclude_namespaces: Skip these namespaces

        Returns:
            Dictionary with sync statistics (created, updated, failed)
        """
        stats = {"created": 0, "updated": 0, "failed": 0}
        include_ns = set(include_namespaces) if include_namespaces else None
        exclude_ns = set(exclude_namespaces or [])

        try:
            catalog = self.scan_all_tables()

            for namespace, tables in catalog.items():
                # Filter namespaces
                if include_ns and namespace not in include_ns:
                    continue
                if namespace in exclude_ns:
                    continue

                logger.info(f"Syncing namespace: {namespace} ({len(tables)} tables)")

                for table_metadata in tables:
                    try:
                        table = self.extract_openmetadata_table(namespace, table_metadata)
                        om_client.create_or_update_table(namespace, table)
                        stats["created"] += 1

                    except Exception as e:
                        logger.error(
                            f"Failed to sync table {namespace}.{table_metadata.get('name')}: {e}"
                        )
                        stats["failed"] += 1

        except Exception as e:
            logger.error(f"Error during sync: {e}")

        logger.info(
            f"Nessie sync completed: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )

        return stats
