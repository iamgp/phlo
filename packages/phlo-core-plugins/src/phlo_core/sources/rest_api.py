"""REST API source connector plugin."""

from typing import Any

import requests

from phlo.plugins import PluginMetadata, SourceConnectorPlugin


class RestAPIPlugin(SourceConnectorPlugin):
    """Generic REST API source connector."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="rest_api",
            version="0.1.0",
            description="Generic REST API source connector",
            author="Phlo Team",
            tags=["source", "api"],
        )

    def fetch_data(self, config: dict[str, Any]):
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
        return config.get("schema")


def _extract_records(payload: Any, records_path: str | None) -> list[dict[str, Any]]:
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
