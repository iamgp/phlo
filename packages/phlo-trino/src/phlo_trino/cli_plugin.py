"""CLI plugin for Trino commands.

This module registers Trino CLI commands as a plugin for the Phlo CLI.
It exposes the `trino` command group for interacting with the Trino
query engine service.

Classes:
    TrinoCliPlugin: Plugin implementation for Trino CLI commands.

Example:
    The plugin is automatically discovered and registered:
    >>> phlo trino --help
    >>> phlo trino query "SELECT 1"

"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_trino.cli import trino_group


class TrinoCliPlugin(CliCommandPlugin):
    """Register Trino CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="CLI commands for Trino query access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin."""
        return [trino_group]
