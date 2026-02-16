"""CLI plugin for lineage commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_lineage.cli_lineage import lineage_group


class LineageCliPlugin(CliCommandPlugin):
    """Register lineage CLI commands with the plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata: CLI plugin identity and description.
        """
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Lineage CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

        Returns:
            list[click.Command]: Root lineage command group.
        """
        return [lineage_group]
