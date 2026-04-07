"""ClickStack service plugin.

This module defines the ClickStackServicePlugin class which provides
service registration and definition for the ClickStack observability
backend service.
"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class ClickStackServicePlugin(PackageYamlServicePlugin):
    """Service plugin for ClickStack.

    Provides ClickStack (ClickHouse-based observability backend) as a
    managed service within the Phlo services framework. The service
    definition is loaded from the bundled service.yaml file.

    Example:
        Plugin is automatically discovered via entry points.
        Service is started with `phlo services start clickstack`.

    Attributes:
        service_definition: ClickStack Docker Compose configuration.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for ClickStack service registration.

        Returns:
            PluginMetadata: Metadata including name, version, description,
                author, and tags for discovery.

        """
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="ClickStack all-in-one observability backend",
            author="Phlo Team",
            tags=["observability", "logs", "metrics", "traces"],
        )
