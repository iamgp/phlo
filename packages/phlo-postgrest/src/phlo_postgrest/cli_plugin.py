"""CLI plugin for PostgREST commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_postgrest.cli import postgrest


class PostgrestCliPlugin(CliCommandPlugin):
    """Register PostgREST CLI commands with the Phlo plugin system."""

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
