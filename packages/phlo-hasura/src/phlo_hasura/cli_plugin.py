"""CLI plugin for Hasura commands.

This module provides the HasuraCliPlugin class that registers Hasura CLI commands
with the Phlo plugin system. It exposes the `hasura` command group to the main
Phlo CLI.

Example:
    The plugin is automatically discovered and loaded by the plugin system:
    >>> from phlo_hasura.cli_plugin import HasuraCliPlugin
    >>> plugin = HasuraCliPlugin()
    >>> commands = plugin.get_cli_commands()

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_hasura.cli import hasura


class HasuraCliPlugin(CliCommandPlugin):
    """Register Hasura CLI commands with the plugin system.

    This plugin integrates the Hasura command group into the Phlo CLI,
    making all hasura subcommands available through `phlo hasura <command>`.

    Attributes:
        _metadata: Cached plugin metadata for CLI discovery.

    Example:
        >>> plugin = HasuraCliPlugin()
        >>> plugin.metadata.name
        'hasura'
        >>> commands = plugin.get_cli_commands()
        >>> len(commands)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata containing:
                - name: Plugin identifier ("hasura")
                - version: Plugin version ("0.1.0")
                - description: Brief description of the plugin

        Example:
            >>> plugin = HasuraCliPlugin()
            >>> meta = plugin.metadata
            >>> print(meta.name)
            hasura

        """
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="Hasura CLI commands for metadata management",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

        Returns:
            List containing the root Hasura command group.
            This group includes all hasura subcommands (track, relationships,
            permissions, auto_setup, export, apply, status, sync-permissions).

        Example:
            >>> plugin = HasuraCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> len(commands)
            1
            >>> commands[0].name
            'hasura'

        """
        return [hasura]
