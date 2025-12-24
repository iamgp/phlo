"""CLI plugin for lineage commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_lineage.cli_lineage import lineage_group


class LineageCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="lineage",
            version="0.1.0",
            description="Lineage CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [lineage_group]
