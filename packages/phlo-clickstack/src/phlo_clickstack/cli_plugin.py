"""CLI plugin for ClickStack commands.

This module defines the ClickStackCliPlugin class which registers CLI commands
for interacting with the ClickStack ClickHouse service.
"""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_clickstack.cli import clickstack_group


class ClickStackCliPlugin(CliCommandPlugin):
    """Register ClickStack CLI commands.

    This plugin provides CLI commands for querying and managing the
    ClickStack ClickHouse service instance.

    Example:
        Registered automatically when phlo_clickstack is installed.
        Use `phlo clickstack --help` to see available commands.

    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for ClickStack CLI registration.

        Returns:
            PluginMetadata: Metadata including name, version, and description.

        """
        return PluginMetadata(
            name="clickstack",
            version="0.1.0",
            description="CLI commands for ClickStack query access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return ClickStack CLI commands.

        Returns:
            list[click.Command]: List of Click commands provided by this plugin.

        """
        return [clickstack_group]
