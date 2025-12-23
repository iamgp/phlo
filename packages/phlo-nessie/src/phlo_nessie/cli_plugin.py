"""CLI plugin for Nessie-backed catalog commands."""

from __future__ import annotations

import click
from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_nessie.cli_catalog import catalog


class NessieCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="CLI commands for Nessie-backed catalog operations",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [catalog]
