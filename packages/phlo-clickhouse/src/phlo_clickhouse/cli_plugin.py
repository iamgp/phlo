"""CLI plugin for ClickHouse commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata

from phlo_clickhouse.cli import clickhouse_group


class ClickHouseCliPlugin(CliCommandPlugin):
    """Register ClickHouse CLI commands."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="clickhouse",
            version="0.1.0",
            description="CLI commands for ClickHouse data plane access",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [clickhouse_group]
