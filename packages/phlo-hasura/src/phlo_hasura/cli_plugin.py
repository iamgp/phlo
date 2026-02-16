"""CLI plugin for Hasura commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_hasura.cli import hasura


class HasuraCliPlugin(CliCommandPlugin):
    """Register Hasura CLI commands with the plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata: CLI plugin identity and description.
        """
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="Hasura CLI commands for metadata management",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return click commands exposed by this plugin.

        Returns:
            list[click.Command]: Root Hasura command group.
        """
        return [hasura]
