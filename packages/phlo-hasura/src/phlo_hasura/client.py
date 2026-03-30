"""Hasura Metadata API client for table tracking and permission management.

This module provides the HasuraClient class for interacting with Hasura's
Metadata API v1. It handles table tracking, permission management, relationship
creation, and metadata import/export operations.

The client automatically resolves URLs and handles authentication via the
admin secret. All API calls include proper error handling and logging.

Example:
    >>> from phlo_hasura.client import HasuraClient
    >>> client = HasuraClient()
    >>> client.track_table("api", "orders")
    >>> client.create_select_permission("api", "orders", "anon")

Environment Variables:
    HASURA_ADMIN_SECRET: Admin secret for Hasura authentication.
    HASURA_PORT: Port override for Hasura URL resolution.

"""

import json
import os
from typing import Any

import requests
from phlo.config.network import resolve_url
from phlo.logging import get_logger

logger = get_logger(__name__)


def _resolve_hasura_url(url: str) -> str:
    """Resolve Hasura URL, handling Docker hostname resolution.

    Uses the phlo network resolver to handle Docker-internal hostnames
    and port overrides from environment variables.

    Args:
        url: The raw URL to resolve (may contain Docker hostnames like 'hasura').

    Returns:
        The resolved URL with proper hostname and port.

    Example:
        >>> _resolve_hasura_url("http://hasura:8080")
        'http://localhost:8080'  # When running outside Docker

    """
    return resolve_url(url, port_env_var="HASURA_PORT")


class HasuraClient:
    """Client for Hasura Metadata API v1.

    Provides methods for managing Hasura metadata including table tracking,
    permissions, relationships, and metadata import/export. Handles URL
    resolution and authentication automatically.

    Attributes:
        hasura_url: Resolved Hasura GraphQL endpoint URL.
        admin_secret: Admin secret for API authentication.
        metadata_url: Full URL to the metadata API endpoint.

    Example:
        >>> client = HasuraClient()
        >>> client.track_table("api", "users")
        >>> client.create_select_permission("api", "users", "anon")
        >>> metadata = client.export_metadata()

    Environment Variables:
        HASURA_ADMIN_SECRET: Override the default admin secret.
        HASURA_PORT: Override the port in the URL.

    """

    hasura_url: str
    admin_secret: str
    metadata_url: str

    def __init__(self, hasura_url: str | None = None, admin_secret: str | None = None) -> None:
        """Initialize Hasura client.

        Args:
            hasura_url: Hasura GraphQL endpoint URL (default: http://hasura:8080).
                The URL will be resolved to handle Docker hostnames.
            admin_secret: Hasura admin secret (default: from HASURA_ADMIN_SECRET
                env var, or fallback to 'phlo-hasura-admin-secret').

        Example:
            >>> client = HasuraClient()
            >>> client = HasuraClient(
            ...     hasura_url="http://custom:8080",
            ...     admin_secret="my-secret"
            ... )

        """
        raw_url = hasura_url or "http://hasura:8080"
        self.hasura_url = _resolve_hasura_url(raw_url)
        self.admin_secret = admin_secret or os.environ.get(
            "HASURA_ADMIN_SECRET", "phlo-hasura-admin-secret"
        )
        self.metadata_url = f"{self.hasura_url}/v1/metadata"

    def _request(
        self,
        method: str,
        data: dict[str, Any],
        query_type: str | None = None,
    ) -> dict[str, Any]:
        """Make request to Hasura metadata API.

        Internal method for making authenticated requests to the Hasura
        metadata endpoint. Handles errors and provides structured logging.

        Args:
            method: HTTP method (usually "POST" for metadata API).
            data: Request payload dictionary containing type and args.
            query_type: Type of query for error context and logging.

        Returns:
            Response JSON as dictionary.

        Raises:
            requests.RequestException: If the request fails or returns an error status.

        Example:
            >>> data = {
            ...     "type": "export_metadata",
            ...     "args": {}
            ... }
            >>> response = client._request("POST", data, "export_metadata")

        """
        headers = {
            "X-Hasura-Admin-Secret": self.admin_secret,
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method, self.metadata_url, json=data, headers=headers, timeout=30
            )
        except requests.RequestException:
            logger.exception(
                "hasura_metadata_request_transport_failed",
                method=method,
                query_type=query_type or "unknown",
                metadata_url=self.metadata_url,
            )
            raise

        if response.status_code >= 400:
            error_msg = f"Hasura API error ({query_type}): {response.status_code}"
            logger.error(
                "hasura_metadata_request_failed",
                method=method,
                query_type=query_type or "unknown",
                metadata_url=self.metadata_url,
                status_code=response.status_code,
            )
            try:
                error_data = response.json()
                error_msg += f"\n{json.dumps(error_data, indent=2)}"
            except Exception:
                error_msg += f"\n{response.text}"
            raise requests.RequestException(error_msg)

        return response.json()

    def track_table(self, schema: str, table: str, alias: str | None = None) -> dict[str, Any]:
        """Track a table in Hasura.

        Registers a PostgreSQL table with Hasura so it becomes available
        through the GraphQL API. Optionally provides a custom alias for
        the root field names.

        Args:
            schema: Schema name containing the table.
            table: Table name to track.
            alias: Optional alias for GraphQL type name (default: table name).
                When provided, custom root fields are configured.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.track_table("api", "orders")
            >>> client.track_table("api", "order_items", alias="line_items")

        """
        config_dict: dict[str, Any] = {}
        if alias:
            config_dict = {
                "custom_root_fields": {},
                "custom_column_names": {},
            }

        data: dict[str, Any] = {
            "type": "pg_track_table",
            "args": {
                "schema": schema,
                "name": table,
                "configuration": config_dict,
            },
        }

        if alias and isinstance(data["args"], dict):
            config = data["args"].get("configuration")
            if isinstance(config, dict):
                config["custom_root_fields"] = {
                    "select": alias,
                    "select_by_pk": f"{alias}_by_pk",
                    "select_aggregate": f"{alias}_aggregate",
                }

        return self._request("POST", data, f"track_table({schema}.{table})")

    def untrack_table(self, schema: str, table: str) -> dict[str, Any]:
        """Untrack a table from Hasura.

        Removes a previously tracked table from Hasura metadata, making it
        unavailable through the GraphQL API.

        Args:
            schema: Schema name containing the table.
            table: Table name to untrack.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.untrack_table("api", "old_table")

        """
        data = {
            "type": "pg_untrack_table",
            "args": {
                "schema": schema,
                "table": table,
            },
        }

        return self._request("POST", data, f"untrack_table({schema}.{table})")

    def create_select_permission(
        self,
        schema: str,
        table: str,
        role: str,
        filter: dict[str, Any] | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create SELECT permission for a role on a table.

        Grants SELECT access to a specific role on a tracked table.
        Supports row-level security through filter expressions and
        column-level security through column lists.

        Args:
            schema: Schema name containing the table.
            table: Table name to grant permissions on.
            role: Role name to grant permissions to.
            filter: Row-level security filter expression (default: {} for all rows).
            columns: Allowed columns list (default: ["*"] for all columns).

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> # Allow anon to read all rows
            >>> client.create_select_permission("api", "orders", "anon")
            >>> # Allow users to read only their own orders
            >>> client.create_select_permission(
            ...     "api", "orders", "user",
            ...     filter={"user_id": {"_eq": "X-Hasura-User-Id"}},
            ...     columns=["id", "total", "status"]
            ... )

        """
        if filter is None:
            filter = {}

        permission = {
            "columns": columns or ["*"],
            "filter": filter,
            "allow_aggregations": True,
        }

        data = {
            "type": "pg_create_select_permission",
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
                "permission": permission,
            },
        }

        return self._request("POST", data, f"create_select_permission({schema}.{table}.{role})")

    def create_insert_permission(
        self,
        schema: str,
        table: str,
        role: str,
        check: dict[str, Any] | None = None,
        columns: list[str] | None = None,
        set: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create INSERT permission for a role on a table.

        Grants INSERT access to a specific role on a tracked table.
        Supports validation through check expressions and preset values
        that are automatically set on insert.

        Args:
            schema: Schema name containing the table.
            table: Table name to grant permissions on.
            role: Role name to grant permissions to.
            check: Validation check expression (default: {} for no validation).
            columns: Allowed columns for insert (default: ["*"] for all).
            set: Preset values to automatically set on insert (e.g., {"created_by": "x-hasura-user-id"}).

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_insert_permission("api", "orders", "user")
            >>> client.create_insert_permission(
            ...     "api", "orders", "user",
            ...     check={"status": {"_eq": "pending"}},
            ...     set={"created_by": "x-hasura-user-id"}
            ... )

        """
        if check is None:
            check = {}

        permission = {
            "columns": columns or ["*"],
            "check": check,
        }

        if set:
            permission["set"] = set

        data = {
            "type": "pg_create_insert_permission",
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
                "permission": permission,
            },
        }

        return self._request("POST", data, f"create_insert_permission({schema}.{table}.{role})")

    def drop_permission(
        self, schema: str, table: str, role: str, permission_type: str = "select"
    ) -> dict[str, Any]:
        """Drop a permission for a role.

        Removes a previously granted permission from a role on a table.

        Args:
            schema: Schema name containing the table.
            table: Table name to remove permissions from.
            role: Role name to remove permissions for.
            permission_type: Type of permission to drop. One of:
                'select', 'insert', 'update', or 'delete' (default: 'select').

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.
            KeyError: If an invalid permission_type is provided.

        Example:
            >>> client.drop_permission("api", "orders", "anon", "select")
            >>> client.drop_permission("api", "orders", "temp_role", "insert")

        """
        type_map = {
            "select": "pg_drop_select_permission",
            "insert": "pg_drop_insert_permission",
            "update": "pg_drop_update_permission",
            "delete": "pg_drop_delete_permission",
        }

        data = {
            "type": type_map[permission_type],
            "args": {
                "schema": schema,
                "table": table,
                "role": role,
            },
        }

        return self._request(
            "POST",
            data,
            f"drop_{permission_type}_permission({schema}.{table}.{role})",
        )

    def create_object_relationship(
        self,
        schema: str,
        table: str,
        name: str,
        manual_configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create object relationship (many-to-one).

        Creates a relationship where a single row in the source table
        relates to a single row in another table (e.g., order -> customer).

        Args:
            schema: Schema name containing the source table.
            table: Source table name.
            name: Relationship name (e.g., "customer" for orders.customer).
            manual_configuration: Manual configuration dict specifying how to
                relate the tables. Typically contains 'foreign_key_constraint_on'
                with the column name.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_object_relationship(
            ...     "api", "orders", "customer",
            ...     manual_configuration={"foreign_key_constraint_on": "customer_id"}
            ... )

        """
        data = {
            "type": "pg_create_object_relationship",
            "args": {
                "schema": schema,
                "table": table,
                "name": name,
                "using": manual_configuration or {},
            },
        }

        return self._request(
            "POST",
            data,
            f"create_object_relationship({schema}.{table}.{name})",
        )

    def create_array_relationship(
        self,
        schema: str,
        table: str,
        name: str,
        manual_configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create array relationship (one-to-many).

        Creates a relationship where a single row in the source table
        relates to multiple rows in another table (e.g., customer -> orders).

        Args:
            schema: Schema name containing the source table.
            table: Source table name.
            name: Relationship name (e.g., "orders" for customer.orders).
            manual_configuration: Manual configuration dict specifying how to
                relate the tables. Typically contains 'foreign_key_constraint_on'
                with table and column information.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.create_array_relationship(
            ...     "api", "customers", "orders",
            ...     manual_configuration={
            ...         "foreign_key_constraint_on": {
            ...             "table": "orders",
            ...             "column": "customer_id"
            ...         }
            ...     }
            ... )

        """
        data = {
            "type": "pg_create_array_relationship",
            "args": {
                "schema": schema,
                "table": table,
                "name": name,
                "using": manual_configuration or {},
            },
        }

        return self._request(
            "POST",
            data,
            f"create_array_relationship({schema}.{table}.{name})",
        )

    def export_metadata(self) -> dict[str, Any]:
        """Export all Hasura metadata.

        Retrieves the complete Hasura metadata including tracked tables,
        relationships, permissions, event triggers, and remote schemas.

        Returns:
            Complete metadata dictionary containing:
                - version: Metadata format version
                - sources: Data sources and their tables
                - remote_schemas: Remote GraphQL schemas
                - actions: Custom actions
                - cron_triggers: Scheduled triggers
                - etc.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> metadata = client.export_metadata()
            >>> len(metadata.get("sources", []))
            1

        """
        data = {"type": "export_metadata", "args": {}}
        return self._request("POST", data, "export_metadata")

    def apply_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Apply metadata to Hasura.

        Replaces the current Hasura metadata with the provided metadata
        dictionary. This is a destructive operation that will remove
        any existing metadata not present in the input.

        Args:
            metadata: Complete metadata dictionary to apply.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> metadata = client.export_metadata()
            >>> # Modify metadata...
            >>> response = client.apply_metadata(metadata)

        """
        data = {"type": "replace_metadata", "args": {"metadata": metadata}}
        return self._request("POST", data, "apply_metadata")

    def reload_metadata(self) -> dict[str, Any]:
        """Reload metadata from database.

        Forces Hasura to reload its metadata from the underlying database.
        Useful when database schema changes occur outside of Hasura.

        Returns:
            API response dictionary.

        Raises:
            requests.RequestException: If the API call fails.

        Example:
            >>> client.reload_metadata()  # After manual DB schema changes

        """
        data = {"type": "reload_metadata", "args": {}}
        return self._request("POST", data, "reload_metadata")

    def get_tables(self, schema: str) -> list[str]:
        """Get list of tables in a schema.

        Queries the current metadata to find all tracked tables
        within a specific schema.

        Args:
            schema: Schema name to query.

        Returns:
            List of table names tracked in the specified schema.

        Example:
            >>> tables = client.get_tables("api")
            >>> print(tables)
            ['orders', 'customers', 'products']

        """
        metadata = self.export_metadata()

        tables = []
        for source in metadata.get("sources", []):
            if source.get("name") == "default":
                for table in source.get("tables", []):
                    if table.get("table", {}).get("schema") == schema:
                        tables.append(table["table"]["name"])

        return tables

    def get_tracked_tables(self) -> dict[str, list[str]]:
        """Get all tracked tables by schema.

        Returns a mapping of schema names to lists of tracked tables
        across all data sources in the metadata.

        Returns:
            Dictionary mapping schema names to lists of table names.
            Example: {"api": ["orders", "customers"], "public": ["users"]}

        Example:
            >>> tracked = client.get_tracked_tables()
            >>> for schema, tables in tracked.items():
            ...     print(f"{schema}: {len(tables)} tables")

        """
        metadata = self.export_metadata()
        tracked = {}

        for source in metadata.get("sources", []):
            if source.get("name") == "default":
                for table in source.get("tables", []):
                    schema = table.get("table", {}).get("schema", "public")
                    table_name = table["table"]["name"]

                    if schema not in tracked:
                        tracked[schema] = []

                    tracked[schema].append(table_name)

        return tracked
