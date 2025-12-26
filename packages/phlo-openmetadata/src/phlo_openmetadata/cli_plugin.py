"""CLI plugin for OpenMetadata integration."""

from __future__ import annotations

import click
from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_openmetadata.cli_openmetadata import openmetadata


class OpenMetadataCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="openmetadata",
            version="0.1.0",
            description="CLI commands for OpenMetadata synchronization",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [openmetadata]
