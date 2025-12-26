"""CLI plugin for PostgREST commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_postgrest.cli import postgrest


class PostgrestCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="postgrest",
            version="0.1.0",
            description="PostgREST CLI commands and helpers",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [postgrest]
