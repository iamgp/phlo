"""CLI plugin for Dagster-related commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dagster.cli_backfill import backfill
from phlo_dagster.cli_dev import dev
from phlo_dagster.cli_logs import logs
from phlo_dagster.cli_materialize import materialize
from phlo_dagster.cli_status import status


class DagsterCliPlugin(CliCommandPlugin):
    """Expose Dagster workflow commands to the Phlo CLI plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin identity metadata for discovery.

        Returns:
            Plugin metadata for Dagster CLI commands.
        """
        return PluginMetadata(
            name="dagster",
            version="0.1.0",
            description="Dagster CLI commands (logs, status, backfill, materialize)",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by the Dagster plugin.

        Returns:
            Ordered list of Dagster-related Click commands.
        """
        return [dev, logs, status, backfill, materialize]
