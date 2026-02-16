"""REST API source connector plugin."""

from typing import Any

import requests

from phlo.plugins import PluginMetadata, SourceConnectorPlugin


class RestAPIPlugin(SourceConnectorPlugin):
    """Generic REST API source connector."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Metadata for the REST API source connector plugin.
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

        Args:
            config: Source configuration containing request and extraction options.

        Yields:
            dict[str, Any]: Records extracted from the response payload.
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
        """Get optional static schema for records.

        Args:
            config: Source configuration that may include a schema mapping.

        Returns:
            dict[str, str] | None: Schema mapping if present.
        """
        return config.get("schema")


def _extract_records(payload: Any, records_path: str | None) -> list[dict[str, Any]]:
    """Extract record objects from a JSON payload.

    Args:
        payload: Parsed JSON response payload.
        records_path: Dot-separated path to list or object records in payload.

    Returns:
        list[dict[str, Any]]: Normalized list of record objects.

    Raises:
        ValueError: If records path is missing or payload shape is unsupported.
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
