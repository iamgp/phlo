"""CLI plugin for PostgreSQL commands.

This module provides the CLI plugin implementation that registers PostgreSQL
commands with the phlo CLI system. It exposes the postgres command group and
its subcommands (query, dump, restore, vacuum) to the main phlo CLI.

Example:
    >>> from phlo_postgres.cli_plugin import PostgresCliPlugin
    >>> plugin = PostgresCliPlugin()
    >>> commands = plugin.get_cli_commands()
    >>> print(commands[0].name)
    postgres

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_postgres.cli import postgres_group


class PostgresCliPlugin(CliCommandPlugin):
    """CLI plugin that registers PostgreSQL commands with the phlo CLI.

    This plugin provides the main entry point for PostgreSQL-related CLI
    commands. It registers the postgres command group which includes
    subcommands for querying, dumping, restoring, and maintaining PostgreSQL
    databases.

    Attributes:
        None (uses class-level plugin registration).

    Example:
        >>> plugin = PostgresCliPlugin()
        >>> print(plugin.metadata.name)
        postgres
        >>> commands = plugin.get_cli_commands()
        >>> print([cmd.name for cmd in commands])
        ['postgres']

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for the PostgreSQL CLI plugin.

        Returns:
            PluginMetadata: Metadata describing the CLI plugin including name,
                version, and description for plugin discovery.

        Example:
            >>> plugin = PostgresCliPlugin()
            >>> meta = plugin.metadata
            >>> print(f"{meta.name} v{meta.version}")
            postgres v0.1.0
            >>> print(meta.description)
            CLI commands for PostgreSQL service access

        """
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="CLI commands for PostgreSQL service access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by this plugin.

        Returns:
            list[click.Command]: List of Click command objects to register
                with the main phlo CLI. Currently provides the postgres
                command group which includes query, dump, restore, and
                vacuum subcommands.

        Example:
            >>> plugin = PostgresCliPlugin()
            >>> commands = plugin.get_cli_commands()
            >>> cmd = commands[0]
            >>> print(cmd.name)
            postgres
            >>> print([c.name for c in cmd.commands.values()])
            ['query', 'dump', 'restore', 'vacuum']

        """
        return [postgres_group]
