"""CLI plugin for Dagster-related commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dagster.cli_backfill import backfill
from phlo_dagster.cli_logs import logs
from phlo_dagster.cli_materialize import materialize
from phlo_dagster.cli_status import status


class DagsterCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Dagster CLI commands (logs, status, backfill, materialize)",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [logs, status, backfill, materialize]
