"""CLI plugin for dbt-related commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dbt.cli_publishing import publishing


class DbtCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [publishing]
