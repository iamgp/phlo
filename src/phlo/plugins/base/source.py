"""
Source connector plugin classes.

This module defines plugin types for data ingestion from external sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from phlo.plugins.base.plugin import Plugin


class SourceConnectorPlugin(Plugin, ABC):
    """
    Base class for source connector plugins.

    Source connectors enable ingesting data from external sources
    like APIs, databases, file systems, etc.

    Example:
        ```python
        class GitHubConnector(SourceConnectorPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="github",
                    version="1.0.0",
                    description="Fetch data from GitHub API",
                    author="Phlo Team",
                )

            def fetch_data(self, config: dict) -> Iterator[dict]:
                api_token = config["api_token"]
                repo = config["repo"]

                # Fetch data from GitHub API
                for event in fetch_github_events(api_token, repo):
                    yield event

            def get_schema(self, config: dict) -> dict:
                return {
                    "id": "string",
                    "type": "string",
                    "created_at": "timestamp",
                    "actor": "object",
                }
        ```
    """

    @abstractmethod
    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """
        Fetch data from the source.

        This method should yield dictionaries representing individual records.
        It will be called by Phlo's ingestion framework to load data.

        Args:
            config: Configuration for this fetch operation, including:
                - Connection parameters
                - Query/filter parameters
                - Pagination settings
                - Authentication credentials

        Yields:
            Dict representing a single record

        Example:
            ```python
            def fetch_data(self, config: dict) -> Iterator[dict]:
                api_url = config["api_url"]
                api_key = config["api_key"]

                response = requests.get(api_url, headers={"Authorization": f"Bearer {api_key}"})
                for item in response.json()["items"]:
                    yield {
                        "id": item["id"],
                        "value": item["value"],
                        "timestamp": item["created_at"],
                    }
            ```
        """
        pass

    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """
        Get the schema of data returned by this connector.

        This method is optional but recommended. It helps with:
        - Type inference
        - Data validation
        - Documentation

        Args:
            config: Configuration for the source

        Returns:
            Dictionary mapping column names to types (e.g., {"id": "string", "count": "int"})
            or None if schema is dynamic/unknown

        Example:
            ```python
            def get_schema(self, config: dict) -> dict:
                return {
                    "id": "string",
                    "temperature": "float",
                    "timestamp": "timestamp",
                    "location": "string",
                }
            ```
        """
        return None

    def test_connection(self, config: dict[str, Any]) -> bool:
        """
        Test if the source is reachable with given configuration.

        This method is optional but recommended for debugging.

        Args:
            config: Configuration to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            iterator = iter(self.fetch_data(config))
            next(iterator)
            return True
        except StopIteration:
            return True
        except Exception:
            return False
