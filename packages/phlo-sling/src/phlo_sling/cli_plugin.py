"""CLI plugin for Sling commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_sling.cli_commands import sling_group


class SlingCliPlugin(CliCommandPlugin):
    """Expose Sling CLI command groups to the Phlo plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery."""
        return PluginMetadata(
            name="sling",
            version="0.1.0",
            description="Sling replication CLI commands for Phlo",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin."""
        return [sling_group]
