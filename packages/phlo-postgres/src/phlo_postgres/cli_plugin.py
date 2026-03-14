"""CLI plugin for PostgreSQL commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_postgres.cli import postgres_group


class PostgresCliPlugin(CliCommandPlugin):
    """Register PostgreSQL CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="postgres",
            version="0.1.0",
            description="CLI commands for PostgreSQL service access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [postgres_group]
