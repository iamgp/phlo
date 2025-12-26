"""CLI plugin for Hasura commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_hasura.cli import hasura


class HasuraCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="hasura",
            version="0.1.0",
            description="Hasura CLI commands for metadata management",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [hasura]
