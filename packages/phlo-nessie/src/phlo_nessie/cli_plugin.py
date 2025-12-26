"""CLI plugin for Nessie commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_nessie.cli_branch import branch
from phlo_nessie.cli_catalog import catalog


class NessieCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="nessie",
            version="0.1.0",
            description="Nessie catalog and branch management commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [catalog, branch]
