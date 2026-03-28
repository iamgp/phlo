"""OpenMetadata service plugin.

Provides OpenMetadata as a managed service within the Phlo plugin framework.
This plugin exposes service configuration and metadata for the OpenMetadata
data catalog and governance platform.

Example:
    >>> from phlo_openmetadata.plugin import OpenMetadataServicePlugin
    >>> plugin = OpenMetadataServicePlugin()
    >>> plugin.metadata.name
    'openmetadata'

"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

from phlo.plugins import PluginMetadata, ServicePlugin


class OpenMetadataServicePlugin(ServicePlugin):
    """Service plugin for OpenMetadata.

    Integrates OpenMetadata data catalog and governance platform into
    the Phlo service management system. Provides service definition
    metadata for container orchestration.

    Attributes:
        metadata: PluginMetadata containing plugin identification information.
        service_definition: YAML service configuration for deployment.

    Example:
        >>> plugin = OpenMetadataServicePlugin()
        >>> defn = plugin.service_definition
        >>> defn['services']
        {...}

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for OpenMetadata service registration.

        Returns:
            PluginMetadata: Metadata with name, version, description, and tags.

        """
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="OpenMetadata data catalog and governance",
            author="Phlo Team",
            tags=["catalog", "governance", "metadata"],
        )

    @property
    def service_definition(self) -> dict[str, Any]:
        """Load and return the OpenMetadata service definition.

        Returns:
            dict[str, Any]: Dictionary containing Docker Compose service
                configuration parsed from service.yaml resource file.

        Raises:
            FileNotFoundError: If service.yaml is missing.
            yaml.YAMLError: If service.yaml is malformed.

        """
        service_path = resources.files("phlo_openmetadata").joinpath("service.yaml")
        return yaml.safe_load(service_path.read_text(encoding="utf-8"))
