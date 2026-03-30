"""REST API source connector plugin.

This module provides the RestAPIPlugin, a generic source connector for fetching
data from REST API endpoints. It supports configurable HTTP requests with
custom headers, query parameters, timeouts, and flexible response parsing.

Features:
    - HTTP GET requests with configurable headers and query parameters
    - Customizable timeout settings
    - Flexible response parsing with dot-notation path support
    - Automatic error handling with HTTP status code checking
    - Support for both list and object response payloads
    - Optional static schema retrieval

Example:
    Using the REST API plugin::

        from phlo_core.sources.rest_api import RestAPIPlugin

        # Create the plugin
        plugin = RestAPIPlugin()

        # Configure a data fetch
        config = {
            "url": "https://api.example.com/v1/users",
            "headers": {
                "Authorization": "Bearer your-api-token",
                "Accept": "application/json"
            },
            "params": {"page": 1, "per_page": 100},
            "timeout": 30,
            "records_path": "data.users",  # Dot-notation path to records
            "schema": {
                "id": "int",
                "name": "str",
                "email": "str"
            }
        }

        # Fetch and process records
        for record in plugin.fetch_data(config):
            print(f"User: {record['name']}")

        # Get schema if available
        schema = plugin.get_schema(config)

"""

from typing import Any

import requests

from phlo.plugins import PluginMetadata, SourceConnectorPlugin


class RestAPIPlugin(SourceConnectorPlugin):
    """Generic REST API source connector for fetching data from HTTP endpoints.

    This plugin provides a flexible interface for connecting to REST APIs and
    extracting data. It handles HTTP request configuration, response parsing,
    and error handling automatically.

    The connector supports:
        - Custom HTTP headers for authentication and content negotiation
        - Query parameters for filtering and pagination
        - Configurable request timeouts
        - Dot-notation path extraction for nested JSON responses
        - Both list and single-object response formats

    Attributes:
        metadata: PluginMetadata containing name, version, description,
            author, and tags for this plugin.

    Example:
        Basic usage with a simple API::

            from phlo_core.sources.rest_api import RestAPIPlugin

            plugin = RestAPIPlugin()
            config = {
                "url": "https://jsonplaceholder.typicode.com/posts",
                "timeout": 10
            }

            for post in plugin.fetch_data(config):
                print(post["title"])

        Advanced usage with authentication and nested data::

            config = {
                "url": "https://api.example.com/data",
                "headers": {"Authorization": "Bearer token"},
                "params": {"date": "2024-01-01"},
                "records_path": "response.data.items",
                "timeout": 60
            }

            records = list(plugin.fetch_data(config))

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the REST API source connector.

        Returns:
            PluginMetadata: Metadata including name ("rest_api"),
                version ("0.1.0"), description ("Generic REST API source connector"),
                author ("Phlo Team"), and tags (["source", "api"]).

        """
        return PluginMetadata(
            name="rest_api",
            version="0.1.0",
            description="Generic REST API source connector",
            author="Phlo Team",
            tags=["source", "api"],
        )

    def fetch_data(self, config: dict[str, Any]):
        """Fetch records from a REST API endpoint.

        Makes an HTTP GET request to the configured URL and yields records
        extracted from the response. Handles request configuration, error
        checking, and response parsing automatically.

        Args:
            config: Source configuration dictionary containing:
                - url (str, required): The API endpoint URL to fetch from.
                - headers (dict, optional): HTTP headers to include in the request.
                    Defaults to empty dict.
                - params (dict, optional): Query parameters to append to the URL.
                    Defaults to empty dict.
                - timeout (int, optional): Request timeout in seconds.
                    Defaults to 30.
                - records_path (str, optional): Dot-separated path to the records
                    within the JSON response. If not provided, assumes the response
                    is either a list of records or a single record object.

        Yields:
            dict[str, Any]: Individual record dictionaries extracted from
            the response payload. Each yielded item represents one record
            ready for processing.

        Raises:
            requests.RequestException: If the HTTP request fails or returns
                a non-2xx status code.
            ValueError: If the records_path is specified but not found in
                the response, or if the payload format is unsupported.

        Example:
            Fetch data with authentication::

                config = {
                    "url": "https://api.example.com/users",
                    "headers": {"Authorization": "Bearer token123"},
                    "timeout": 30
                }

                for user in plugin.fetch_data(config):
                    process_user(user)

            Fetch nested data from complex response::

                config = {
                    "url": "https://api.example.com/complex",
                    "records_path": "response.data.records",
                    "params": {"limit": 100}
                }

                records = list(plugin.fetch_data(config))

        """
        url = config["url"]
        headers = config.get("headers", {})
        params = config.get("params", {})
        timeout = config.get("timeout", 30)
        records_path = config.get("records_path")

        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()

        payload = response.json()
        records = _extract_records(payload, records_path)
        for record in records:
            yield record

    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """Retrieve optional static schema from configuration.

        Extracts and returns a schema mapping if one was provided in the
        configuration. This allows users to optionally specify expected
        column names and types alongside the source configuration.

        Args:
            config: Source configuration dictionary that may include a
                "schema" key mapping column names to type strings.

        Returns:
            dict[str, str] | None: Schema mapping dictionary if present in
            config, where keys are column names and values are type strings.
            Returns None if no schema was configured.

        Example:
            Get schema from config::

                config = {
                    "url": "https://api.example.com/data",
                    "schema": {
                        "id": "int",
                        "name": "str",
                        "created_at": "datetime"
                    }
                }

                schema = plugin.get_schema(config)
                # Returns: {"id": "int", "name": "str", "created_at": "datetime"}

            Without schema in config::

                config = {"url": "https://api.example.com/data"}
                schema = plugin.get_schema(config)  # Returns None

        """
        return config.get("schema")


def _extract_records(payload: Any, records_path: str | None) -> list[dict[str, Any]]:
    """Extract record objects from a JSON response payload.

    Parses the JSON response and extracts records based on an optional
    dot-notation path. Supports both list responses (multiple records)
    and object responses (single record).

    Args:
        payload: Parsed JSON response payload from the API. This should be
            the result of calling ``response.json()`` on a requests response.
        records_path: Dot-separated path to the list or object records in
            the payload (e.g., "data.users" or "response.items"). If None,
            the payload itself is expected to be either a list of records
            or a single record object.

    Returns:
        list[dict[str, Any]]: Normalized list of record dictionaries.
        If the payload contained a single object, it is wrapped in a list.
        If the payload contained a list, it is returned as-is.

    Raises:
        ValueError: If records_path is specified but the path cannot be
            traversed in the payload, or if the final payload shape is
            neither a list nor a dictionary.

    Example:
        Extract from list response::

            payload = [{"id": 1}, {"id": 2}]
            records = _extract_records(payload, None)
            # Returns: [{"id": 1}, {"id": 2}]

        Extract from nested response::

            payload = {"data": {"users": [{"id": 1}, {"id": 2}]}}
            records = _extract_records(payload, "data.users")
            # Returns: [{"id": 1}, {"id": 2}]

        Extract single object::

            payload = {"id": 1, "name": "test"}
            records = _extract_records(payload, None)
            # Returns: [{"id": 1, "name": "test"}]

        Path not found::

            payload = {"data": {}}
            records = _extract_records(payload, "data.missing")
            # Raises: ValueError

    """
    if records_path:
        current = payload
        for key in records_path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise ValueError(f"records_path '{records_path}' not found in payload")
        payload = current

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]

    raise ValueError("Unsupported payload shape for REST API response")
