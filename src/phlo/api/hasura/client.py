"""Hasura Metadata API client for table tracking and permission management."""

import json
from typing import Any

import requests


class HasuraClient:
    """Client for Hasura Metadata API v1."""

    hasura_url: str
    admin_secret: str
    metadata_url: str

    def __init__(
        self, hasura_url: str | None = None, admin_secret: str | None = None
    ) -> None:
        """Initialize Hasura client.

        Args:
            hasura_url: Hasura GraphQL endpoint URL (default: http://localhost:8080)
            admin_secret: Hasura admin secret (default: minio from config)
        """
        self.hasura_url = hasura_url or "http://hasura:8080"
        self.admin_secret = admin_secret or "hasura-secret-key"
        self.metadata_url = f"{self.hasura_url}/v1/metadata"

    def _request(
        self,
        method: str,
        data: dict[str, Any],
        query_type: str | None = None,
    ) -> dict[str, Any]:
        """Make request to Hasura metadata API.

        Args:
            method: HTTP method (usually POST)
            data: Request payload
            query_type: Type of query for error context

        Returns:
            Response JSON

        Raises:
            requests.RequestException: If request fails
        """
        headers = {
            "X-Hasura-Admin-Secret": self.admin_secret,
            "Content-Type": "application/json",
        }

        response = requests.request(
            method, self.metadata_url, json=data, headers=headers, timeout=30
        )

        if response.status_code >= 400:
            error_msg = f"Hasura API error ({query_type}): {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f"\n{json.dumps(error_data, indent=2)}"
            except Exception:
                error_msg += f"\n{response.text}"
            raise requests.RequestException(error_msg)

        return response.json()

    def track_table(
        self, schema: str, table: str, alias: str | None = None
    ) -> dict[str, Any]:
        """Track a table in Hasura.

        Args:
            schema: Schema name
            table: Table name
            alias: Optional alias for GraphQL type (default: table name)

        Returns:
            API response
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

        Args:
            schema: Schema name
            table: Table name

        Returns:
            API response
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

        Args:
            schema: Schema name
            table: Table name
            role: Role name
            filter: Row-level security filter (default: {})
            columns: Allowed columns (default: all)

        Returns:
            API response
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

        return self._request(
            "POST", data, f"create_select_permission({schema}.{table}.{role})"
        )

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

        Args:
            schema: Schema name
            table: Table name
            role: Role name
            check: Check expression (default: {})
            columns: Allowed columns for insert (default: all)
            set: Preset values

        Returns:
            API response
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

        return self._request(
            "POST", data, f"create_insert_permission({schema}.{table}.{role})"
        )

    def drop_permission(
        self, schema: str, table: str, role: str, permission_type: str = "select"
    ) -> dict[str, Any]:
        """Drop a permission for a role.

        Args:
            schema: Schema name
            table: Table name
            role: Role name
            permission_type: 'select', 'insert', 'update', or 'delete'

        Returns:
            API response
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

        Args:
            schema: Schema name
            table: Table name
            name: Relationship name
            manual_configuration: Manual configuration dict

        Returns:
            API response
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

        Args:
            schema: Schema name
            table: Table name
            name: Relationship name
            manual_configuration: Manual configuration dict

        Returns:
            API response
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

        Returns:
            Complete metadata dictionary
        """
        data = {"type": "export_metadata", "args": {}}
        return self._request("POST", data, "export_metadata")

    def apply_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Apply metadata to Hasura.

        Args:
            metadata: Metadata dictionary

        Returns:
            API response
        """
        data = {"type": "replace_metadata", "args": {"metadata": metadata}}
        return self._request("POST", data, "apply_metadata")

    def reload_metadata(self) -> dict[str, Any]:
        """Reload metadata from database.

        Returns:
            API response
        """
        data = {"type": "reload_metadata", "args": {}}
        return self._request("POST", data, "reload_metadata")

    def get_tables(self, schema: str) -> list[str]:
        """Get list of tables in a schema.

        Args:
            schema: Schema name

        Returns:
            List of table names
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

        Returns:
            Dictionary of schema -> list of table names
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
