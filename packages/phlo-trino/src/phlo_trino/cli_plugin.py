"""CLI plugin for Trino commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_trino.cli import trino_group


class TrinoCliPlugin(CliCommandPlugin):
    """Register Trino CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="trino",
            version="0.1.0",
            description="CLI commands for Trino query access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [trino_group]
