"""CLI plugin for ClickHouse commands.

This module provides a CLI plugin that registers ClickHouse-specific commands
with the Phlo CLI framework, enabling users to interact with ClickHouse
databases directly from the command line.

Example:
    The plugin is automatically discovered by Phlo's plugin system:

    >>> from phlo_clickhouse.cli_plugin import ClickHouseCliPlugin
    >>> plugin = ClickHouseCliPlugin()
    >>> plugin.metadata.name
    'clickhouse'

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_clickhouse.cli import clickhouse_group


class ClickHouseCliPlugin(CliCommandPlugin):
    """Register ClickHouse CLI commands with the Phlo CLI.

    This plugin integrates ClickHouse commands into the Phlo CLI, providing
    access to query execution, status checks, and other ClickHouse operations.

    Attributes:
        None

    Example:
        >>> plugin = ClickHouseCliPlugin()
        >>> commands = plugin.get_cli_commands()
        >>> len(commands)
        1

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI registration.

        Returns:
            PluginMetadata containing name, version, and description.

        Example:
            >>> plugin = ClickHouseCliPlugin()
            >>> meta = plugin.metadata
            >>> meta.name
            'clickhouse'

        """
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="CLI commands for ClickHouse data plane access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return list of ClickHouse CLI command groups.

        Returns:
            List containing the clickhouse command group.

        Example:
            >>> plugin = ClickHouseCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> [cmd.name for cmd in commands]
            ['clickhouse']

        """
        return [clickhouse_group]
