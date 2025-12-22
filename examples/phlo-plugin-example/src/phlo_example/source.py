"""
Example source connector plugin using JSONPlaceholder API.

Demonstrates:
- Fetching data from an external API
- Error handling and connection testing
- Schema definition
- Configuration validation
"""

from typing import Any, Iterator

import requests

from phlo.plugins import PluginMetadata, SourceConnectorPlugin


class JSONPlaceholderSource(SourceConnectorPlugin):
    """
    Source connector for JSONPlaceholder API.

    Fetches posts, comments, or other data from the free JSONPlaceholder API.
    Useful for testing and demonstrations.

    Configuration:
        {
            "base_url": "https://jsonplaceholder.typicode.com",  # API base URL
            "resource": "posts",  # Resource to fetch (posts, comments, users, etc.)
            "limit": 10,  # Maximum number of items to fetch (0 = no limit)
        }
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="jsonplaceholder",
            version="1.0.0",
            description="Fetch data from JSONPlaceholder API",
            author="Phlo Team",
            homepage="https://github.com/iamgp/phlo",
            tags=["api", "example", "public"],
            license="MIT",
        )

    def fetch_data(self, config: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """
        Fetch data from JSONPlaceholder API.

        Args:
            config: Configuration dictionary with:
                - base_url: API base URL (default: https://jsonplaceholder.typicode.com)
                - resource: Resource to fetch (default: posts)
                - limit: Max items to fetch (default: 0 = all)

        Yields:
            Dictionary representing each item from the API

        Raises:
            ValueError: If configuration is invalid
            requests.RequestException: If API request fails
        """
        # Validate configuration
        if not self.validate_config(config):
            raise ValueError("Invalid configuration")

        base_url = config.get("base_url", "https://jsonplaceholder.typicode.com")
        resource = config.get("resource", "posts")
        limit = config.get("limit", 0)

        # Build API URL
        url = f"{base_url}/{resource}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            items = response.json()

            # Ensure items is a list
            if not isinstance(items, list):
                items = [items]

            # Apply limit if specified
            if limit > 0:
                items = items[:limit]

            # Yield each item
            for item in items:
                yield item

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch from {url}: {e}")

    def get_schema(self, config: dict[str, Any]) -> dict[str, str] | None:
        """
        Get expected schema for the resource.

        Returns:
            Dictionary mapping column names to their types
        """
        resource = config.get("resource", "posts")

        schemas = {
            "posts": {
                "userId": "int",
                "id": "int",
                "title": "string",
                "body": "string",
            },
            "comments": {
                "postId": "int",
                "id": "int",
                "name": "string",
                "email": "string",
                "body": "string",
            },
            "users": {
                "id": "int",
                "name": "string",
                "username": "string",
                "email": "string",
                "address": "object",
                "phone": "string",
                "website": "string",
            },
        }

        return schemas.get(resource, None)

    def test_connection(self, config: dict[str, Any]) -> bool:
        """
        Test if the API is accessible.

        Args:
            config: Configuration dictionary

        Returns:
            True if connection successful, False otherwise
        """
        try:
            base_url = config.get("base_url", "https://jsonplaceholder.typicode.com")
            resource = config.get("resource", "posts")
            url = f"{base_url}/{resource}"

            response = requests.get(url, timeout=5)
            return response.status_code == 200

        except Exception:
            return False

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(config, dict):
            return False

        # Validate base_url if provided
        base_url = config.get("base_url")
        if base_url and not isinstance(base_url, str):
            return False

        # Validate resource if provided
        resource = config.get("resource")
        if resource and not isinstance(resource, str):
            return False

        # Validate limit if provided
        limit = config.get("limit", 0)
        if not isinstance(limit, int) or limit < 0:
            return False

        return True
