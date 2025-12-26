"""
OpenMetadata REST API client for metadata synchronization.

Provides authenticated access to OpenMetadata for:
- Creating/updating table entities
- Publishing lineage information
- Managing quality test results
- Syncing column-level documentation
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


@dataclass
class OpenMetadataColumn:
    """Represents a column in OpenMetadata."""

    name: str
    displayName: Optional[str] = None
    description: Optional[str] = None
    dataType: str = "UNKNOWN"
    dataLength: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    tags: Optional[list[dict[str, Any]]] = None
    constraint: Optional[str] = None
    ordinalPosition: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class OpenMetadataTable:
    """Represents a table entity in OpenMetadata."""

    name: str
    description: Optional[str] = None
    columns: Optional[list[OpenMetadataColumn]] = None
    tableType: str = "Regular"
    owner: Optional[dict[str, Any]] = None
    tags: Optional[list[dict[str, Any]]] = None
    sourceUrl: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict, converting columns to dicts."""
        data = {
            "name": self.name,
            "tableType": self.tableType,
        }
        if self.description:
            data["description"] = self.description
        if self.columns:
            data["columns"] = [col.to_dict() for col in self.columns]
        if self.owner:
            data["owner"] = self.owner
        if self.tags:
            data["tags"] = self.tags
        if self.sourceUrl:
            data["sourceUrl"] = self.sourceUrl
        if self.location:
            data["location"] = self.location
        return data


@dataclass
class OpenMetadataLineageEdge:
    """Represents a lineage edge in OpenMetadata."""

    fromEntity: str
    toEntity: str
    description: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for API submission."""
        data = {"fromEntity": self.fromEntity, "toEntity": self.toEntity}
        if self.description:
            data["description"] = self.description
        return data


class OpenMetadataClient:
    """
    Client for OpenMetadata REST API.

    Provides methods for interacting with OpenMetadata entities and
    publishing metadata, lineage, and quality results.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize OpenMetadata client.

        Args:
            base_url: Base URL of OpenMetadata API (e.g., http://openmetadata:8585/api)
            username: OpenMetadata username
            password: OpenMetadata password
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl
        self.session.headers.update({"Content-Type": "application/json"})

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to OpenMetadata API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            data: JSON payload for request body
            params: Query parameters

        Returns:
            Response JSON
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenMetadata request failed: {method} {endpoint}: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if OpenMetadata is reachable and healthy.

        Returns:
            True if OpenMetadata is healthy, False otherwise
        """
        try:
            response = self.session.request("GET", urljoin(self.base_url + "/", "health"))
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenMetadata health check failed: {e}")
            return False

    def get_table(self, table_fqn: str) -> Optional[dict[str, Any]]:
        """
        Get table entity by fully qualified name.

        Args:
            table_fqn: Fully qualified table name (schema.table)

        Returns:
            Table entity dict or None if not found
        """
        try:
            return self._request("GET", f"/v1/tables/name/{table_fqn}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def search_tables(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Search for tables matching a query.

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            List of matching table entities
        """
        result = self._request(
            "GET",
            "/v1/search/query",
            params={"q": query, "index": "table_search_index", "size": limit},
        )
        hits = result.get("hits", {}).get("hits", [])
        return [hit.get("_source", {}) for hit in hits]

    def create_or_update_table(self, schema_name: str, table: OpenMetadataTable) -> dict[str, Any]:
        """
        Create or update a table entity in OpenMetadata.

        Args:
            schema_name: Database schema name
            table: OpenMetadataTable object

        Returns:
            Created/updated table entity from OpenMetadata
        """
        # Ensure schema exists (create if needed)
        # NOTE: In OpenMetadata, tables are tied to a database schema entity.
        # For now, we assume the schema entity exists or OpenMetadata can resolve it by name.

        table_fqn = f"{schema_name}.{table.name}"

        # Check if table exists
        existing = self.search_tables(table_fqn, limit=10)
        existing_match = next((t for t in existing if t.get("name") == table.name), None)

        payload = table.to_dict()
        payload["databaseSchema"] = {"name": schema_name, "type": "databaseSchema"}

        if existing_match and existing_match.get("id"):
            # Update existing table
            payload["id"] = existing_match["id"]
            return self._request("PUT", "/v1/tables", data=payload)

        # Create new table
        return self._request("POST", "/v1/tables", data=payload)

    def create_lineage(
        self, from_fqn: str, to_fqn: str, description: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create lineage edge between two entities.

        Args:
            from_fqn: Source entity FQN
            to_fqn: Target entity FQN

        Returns:
            Lineage creation result
        """
        edge: dict[str, Any] = {
            "fromEntity": {"fqn": from_fqn, "type": "table"},
            "toEntity": {"fqn": to_fqn, "type": "table"},
        }
        if description:
            edge["description"] = description

        payload = {
            "edge": {
                **edge,
            }
        }
        return self._request("PUT", "/v1/lineage", data=payload)

    def list_databases(self) -> list[dict[str, Any]]:
        """List databases from OpenMetadata."""
        try:
            result = self._request("GET", "/v1/databases")
            data = result.get("data", [])
            return data if isinstance(data, list) else []
        except Exception as exc:
            logger.warning(f"Failed to list databases: {exc}")
            return []

    def add_owner(self, table_fqn: str, owner_name: str) -> dict[str, Any]:
        """Set the owner for a table entity."""
        entity = self.get_table(table_fqn)
        if not entity:
            raise ValueError(f"Table not found: {table_fqn}")

        payload = dict(entity)
        payload["owner"] = {"name": owner_name, "type": "user"}

        return self._request("PUT", "/v1/tables", data=payload)

    def create_test_definition(
        self,
        test_name: str,
        test_type: str,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a test definition in OpenMetadata.

        Args:
            test_name: Name of the test definition
            test_type: Type of test (e.g., nullCheck, rangeCheck)
            description: Optional description
        """
        data = {
            "name": test_name,
            "displayName": test_name,
            "testType": test_type,
            "description": description,
        }
        return self._request("POST", "/v1/testDefinitions", data=data)

    def create_test_case(
        self,
        test_case_name: str,
        table_fqn: str,
        test_definition_name: str,
        parameters: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a test case for a table.
        """
        data: dict[str, Any] = {
            "name": test_case_name,
            "entityLink": f"<#{table_fqn}>",
            "testDefinition": {"name": test_definition_name, "type": "testDefinition"},
            "testSuite": {"name": f"{table_fqn.split('.')[-1]}_suite", "type": "testSuite"},
            "description": description,
        }
        if parameters:
            data["parameterValues"] = [{"name": k, "value": str(v)} for k, v in parameters.items()]
        return self._request("POST", "/v1/testCases", data=data)

    def publish_test_result(
        self,
        test_case_fqn: str,
        result: str,
        test_execution_date: datetime,
        result_value: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Publish a test execution result.
        """
        data = {
            "result": result,
            "testCaseStatus": result,
            "timestamp": int(test_execution_date.timestamp() * 1000),
            "result_value": result_value,
        }
        return self._request(
            "POST",
            f"/v1/testCases/{test_case_fqn}/testCaseResult",
            data=data,
        )

    def close(self) -> None:
        """Close underlying HTTP session."""
        self.session.close()

    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format timestamp for OpenMetadata."""
        return dt.isoformat() + "Z"
