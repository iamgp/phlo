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

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class PgwebServicePlugin(ServicePlugin):
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

    @property
    def service_definition(self) -> dict[str, Any]:
        """Return the Docker service definition for pgweb.

        Reads and parses the service.yaml file bundled with the package
        to provide the Docker Compose service configuration.

        Returns:
            dict[str, Any]: Parsed Docker Compose service definition.

        Raises:
            FileNotFoundError: If the service.yaml file is not found
                in the package resources.
            yaml.YAMLError: If the service.yaml file contains invalid YAML.

        Example:
            >>> plugin = PgwebServicePlugin()
            >>> definition = plugin.service_definition
            >>> 'services' in definition
            True

        """
        service_path = resources.files("phlo_pgweb").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
