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
from dataclasses import dataclass, asdict
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
    """Represents a lineage edge between two entities."""

    from_entity: str  # e.g., "dlt_glucose_entries"
    to_entity: str  # e.g., "stg_glucose_entries"
    entity_type: str = "table"  # table, pipeline, dashboard
    description: Optional[str] = None


class OpenMetadataClient:
    """
    Client for OpenMetadata REST API.

    Handles authentication, table sync, lineage publishing, and quality result tracking.
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
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl

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
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path (e.g., /v1/tables)
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            requests.HTTPError: If request fails
        """
        url = urljoin(self.base_url, endpoint)

        headers = {"Content-Type": "application/json"}

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204:
                return {}

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
            response = self.session.get(
                urljoin(self.base_url, "/v1/health"),
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenMetadata health check failed: {e}")
            return False

    def create_or_update_table(
        self, schema_name: str, table: OpenMetadataTable
    ) -> dict[str, Any]:
        """
        Create or update a table entity in OpenMetadata.

        Args:
            schema_name: Schema/database name containing the table
            table: Table metadata

        Returns:
            Created/updated table entity from OpenMetadata
        """
        data = table.to_dict()
        data["databaseSchema"] = {
            "name": schema_name,
            "type": "databaseSchema",
        }

        try:
            # Try to get existing table first
            existing = self._request(
                "GET", f"/v1/tables?q={table.name}&database={schema_name}"
            )

            if existing.get("data"):
                # Update existing table
                table_id = existing["data"][0]["id"]
                logger.info(f"Updating table {schema_name}.{table.name}")
                return self._request("PUT", f"/v1/tables/{table_id}", data=data)
            else:
                # Create new table
                logger.info(f"Creating table {schema_name}.{table.name}")
                return self._request("POST", "/v1/tables", data=data)

        except Exception as e:
            logger.error(f"Failed to create/update table {schema_name}.{table.name}: {e}")
            raise

    def get_table(self, fqn: str) -> Optional[dict[str, Any]]:
        """
        Get a table entity by fully qualified name.

        Args:
            fqn: Fully qualified name (e.g., schema.table)

        Returns:
            Table entity dict or None if not found
        """
        try:
            return self._request("GET", f"/v1/tables/name/{fqn}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def create_lineage(
        self,
        from_entity_fqn: str,
        to_entity_fqn: str,
        entity_type: str = "table",
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a lineage edge between two entities.

        Args:
            from_entity_fqn: Fully qualified name of source entity
            to_entity_fqn: Fully qualified name of target entity
            entity_type: Type of entities (table, pipeline, etc.)
            description: Optional description of the relationship

        Returns:
            Lineage information from OpenMetadata
        """
        data = {
            "edges": [
                {
                    "fromEntity": {
                        "id": from_entity_fqn,
                        "type": entity_type,
                    },
                    "toEntity": {
                        "id": to_entity_fqn,
                        "type": entity_type,
                    },
                    "description": description,
                }
            ]
        }

        try:
            logger.info(f"Creating lineage: {from_entity_fqn} -> {to_entity_fqn}")
            return self._request("POST", "/v1/lineage", data=data)
        except Exception as e:
            logger.error(f"Failed to create lineage: {e}")
            raise

    def create_test_definition(
        self,
        test_name: str,
        test_type: str,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a test definition in OpenMetadata.

        Args:
            test_name: Name of the test
            test_type: Type of test (e.g., nullCheck, rangeCheck, custom)
            description: Optional test description

        Returns:
            Created test definition
        """
        data = {
            "name": test_name,
            "testPlatforms": ["OpenMetadata"],
            "testCases": [],
            "description": description,
        }

        try:
            logger.info(f"Creating test definition: {test_name}")
            return self._request("POST", "/v1/testDefinitions", data=data)
        except Exception as e:
            logger.error(f"Failed to create test definition {test_name}: {e}")
            raise

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

        Args:
            test_case_name: Name of the test case
            table_fqn: Fully qualified name of table being tested
            test_definition_name: Name of test definition to use
            parameters: Test parameters (e.g., min_value, max_value)
            description: Optional description

        Returns:
            Created test case
        """
        data = {
            "name": test_case_name,
            "entityLink": f"<#{table_fqn}>",
            "testDefinition": {
                "name": test_definition_name,
                "type": "testDefinition",
            },
            "testSuite": {
                "name": f"{table_fqn.split('.')[1]}_suite",  # Create suite per table
                "type": "testSuite",
            },
            "description": description,
        }

        if parameters:
            data["parameterValues"] = [
                {"name": k, "value": str(v)} for k, v in parameters.items()
            ]

        try:
            logger.info(f"Creating test case: {test_case_name}")
            return self._request("POST", "/v1/testCases", data=data)
        except Exception as e:
            logger.error(f"Failed to create test case {test_case_name}: {e}")
            raise

    def publish_test_result(
        self,
        test_case_fqn: str,
        result: str,
        test_execution_date: datetime,
        result_value: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Publish a test execution result.

        Args:
            test_case_fqn: Fully qualified name of test case
            result: Result status (Success, Failed, Aborted)
            test_execution_date: When the test executed
            result_value: Optional result value/metric

        Returns:
            Published test result
        """
        data = {
            "result": result,
            "testCaseStatus": result,
            "timestamp": int(test_execution_date.timestamp() * 1000),
            "result_value": result_value,
        }

        try:
            logger.info(f"Publishing test result: {test_case_fqn} = {result}")
            return self._request(
                "POST",
                f"/v1/testCases/{test_case_fqn}/testCaseResult",
                data=data,
            )
        except Exception as e:
            logger.error(f"Failed to publish test result for {test_case_fqn}: {e}")
            raise

    def list_databases(self) -> list[dict[str, Any]]:
        """
        List all databases in OpenMetadata.

        Returns:
            List of database entities
        """
        try:
            response = self._request("GET", "/v1/databases")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return []

    def list_schemas(self, database_name: str) -> list[dict[str, Any]]:
        """
        List all schemas in a database.

        Args:
            database_name: Name of the database

        Returns:
            List of schema entities
        """
        try:
            response = self._request(
                "GET",
                f"/v1/databaseSchemas?database={database_name}",
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list schemas for {database_name}: {e}")
            return []

    def list_tables(self, schema_fqn: str) -> list[dict[str, Any]]:
        """
        List all tables in a schema.

        Args:
            schema_fqn: Fully qualified name of schema

        Returns:
            List of table entities
        """
        try:
            response = self._request(
                "GET",
                f"/v1/tables?databaseSchema={schema_fqn}",
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list tables in {schema_fqn}: {e}")
            return []

    def add_owner(
        self,
        entity_fqn: str,
        owner_name: str,
        owner_type: str = "user",
    ) -> dict[str, Any]:
        """
        Add an owner to an entity.

        Args:
            entity_fqn: Fully qualified name of entity
            owner_name: Name of the owner
            owner_type: Type of owner (user or team)

        Returns:
            Updated entity
        """
        entity = self.get_table(entity_fqn)
        if not entity:
            raise ValueError(f"Entity not found: {entity_fqn}")

        data = {
            "owner": {
                "name": owner_name,
                "type": owner_type,
            }
        }

        try:
            logger.info(f"Adding owner {owner_name} to {entity_fqn}")
            return self._request(
                "PUT",
                f"/v1/tables/{entity['id']}",
                data=data,
            )
        except Exception as e:
            logger.error(f"Failed to add owner to {entity_fqn}: {e}")
            raise
