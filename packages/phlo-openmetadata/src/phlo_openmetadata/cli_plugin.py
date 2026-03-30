"""CLI plugin for OpenMetadata integration.

This module provides the CLI plugin that registers OpenMetadata commands
with the Phlo CLI framework.

Example:
    >>> from phlo_openmetadata.cli_plugin import OpenMetadataCliPlugin
    >>> plugin = OpenMetadataCliPlugin()
    >>> plugin.metadata.name
    'openmetadata'

"""

from __future__ import annotations

import click
from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_openmetadata.cli_openmetadata import openmetadata


class OpenMetadataCliPlugin(CliCommandPlugin):
    """CLI plugin that registers OpenMetadata commands.

    This plugin integrates OpenMetadata CLI commands into the Phlo CLI,
    providing health checks and sync functionality.

    Attributes:
        metadata: PluginMetadata containing plugin identification information.

    Example:
        >>> plugin = OpenMetadataCliPlugin()
        >>> plugin.metadata.name
        'openmetadata'

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Metadata for the OpenMetadata CLI plugin including
                name, version, and description.

        """
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="CLI commands for OpenMetadata synchronization",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Get CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered OpenMetadata CLI commands
                (health, sync, etc.).

        """
        return [openmetadata]
