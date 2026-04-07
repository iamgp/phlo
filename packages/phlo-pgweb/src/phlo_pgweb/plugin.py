"""Pgweb service plugin implementation.

This module provides the PgwebServicePlugin class which implements
a Phlo service plugin for pgweb, a web-based PostgreSQL database browser.

The plugin reads its Docker Compose service definition from a bundled YAML
file and exposes metadata for integration with Phlo's service management.

Example:
    >>> from phlo_pgweb.plugin import PgwebServicePlugin
    >>> plugin = PgwebServicePlugin()
    >>> print(plugin.metadata.name)
    pgweb
    >>> service_def = plugin.service_definition

"""

from __future__ import annotations

from phlo.plugins import PackageYamlServicePlugin, PluginMetadata


class PgwebServicePlugin(PackageYamlServicePlugin):
    """Service plugin for pgweb PostgreSQL web UI.

    This plugin provides integration with pgweb, a lightweight web-based
    PostgreSQL admin tool. It reads service configuration from a bundled
    service.yaml file and exposes standard Phlo plugin metadata.

    Attributes:
        None

    Example:
        >>> plugin = PgwebServicePlugin()
        >>> metadata = plugin.metadata
        >>> print(metadata.name, metadata.version)
        pgweb 0.1.0
        >>> definition = plugin.service_definition

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the pgweb service.

        Returns:
            PluginMetadata: Plugin metadata containing name, version,
                description, author, and tags.

        Example:
            >>> plugin = PgwebServicePlugin()
            >>> meta = plugin.metadata
            >>> meta.name
            'pgweb'
            >>> meta.tags
            ['admin', 'postgres', 'ui']

        """
        return PluginMetadata(
            name="pgweb",
            version="0.1.0",
            description="Web-based PostgreSQL database browser",
            author="Phlo Team",
            tags=["admin", "postgres", "ui"],
        )
