"""CLI plugin for Dagster-related commands.

This module registers the Dagster CLI command group with Phlo's plugin
system. It exposes commands for workflow management, log access, status
monitoring, and asset materialization.

Commands Provided:
    - dev: Start Dagster development server
    - logs: Access and filter Dagster run logs
    - status: Show asset and service health status
    - backfill: Run partitioned materializations in batch
    - materialize: Materialize assets via Docker

Plugin Registration:
    The DagsterCliPlugin implements CliCommandPlugin and is auto-discovered
    via entry_points (group: phlo.plugins.cli_commands).

Command Organization:
    Commands follow the lifecycle:
    - Development: dev
    - Monitoring: logs, status
    - Execution: materialize, backfill

Integration:
    Commands integrate with Docker containers for execution, ensuring
    consistent environment and resource access.

Example:
    CLI usage::

        phlo dev                    # Start dev server
        phlo logs --follow          # Tail logs
        phlo status --services      # Check service health
        phlo materialize dlt_orders # Materialize asset
        phlo backfill dlt_orders --start-date 2024-01-01 --end-date 2024-01-31

"""

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
