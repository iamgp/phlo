"""CLI plugin for PostgREST commands.

This module provides the CLI plugin that registers PostgREST-specific commands
with the Phlo CLI framework. It integrates with Click to expose view generation
and authentication setup commands.

Classes:
    PostgrestCliPlugin: CLI command registration for PostgREST operations.

Example:
    The plugin enables CLI commands:

    $ phlo postgrest generate-views --help
    $ phlo postgrest setup-auth --force

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_postgrest.cli import postgrest


class PostgrestCliPlugin(CliCommandPlugin):
    """Register PostgREST CLI commands with the Phlo plugin system.

    This plugin bridges the phlo_postgrest CLI commands with Phlo's
    plugin architecture, exposing view generation and authentication
    setup as subcommands under the `phlo postgrest` namespace.

    Attributes:
        metadata (PluginMetadata): Plugin identification and version.

    Example:
        >>> plugin = PostgrestCliPlugin()
        >>> plugin.metadata.name
        'postgrest'
        >>> commands = plugin.get_cli_commands()
        >>> len(commands)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for PostgREST CLI integration.

        Returns:
            PluginMetadata: Plugin identity, version, and description.

        """
        return PluginMetadata(
            name="postgrest",
            version="0.1.0",
            description="PostgREST CLI commands and helpers",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered PostgREST command group.

        """
        return [postgrest]
