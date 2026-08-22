"""Dagster CLI plugin registration.

Wires the dev, logs, status, backfill, and materialize command groups
into the plugin system via cli_command_plugin_class; owns no logic
beyond registration.
"""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_dagster.cli_backfill import backfill
from phlo_dagster.cli_dev import dev
from phlo_dagster.cli_logs import logs
from phlo_dagster.cli_materialize import materialize
from phlo_dagster.cli_status import status


DagsterCliPlugin = cli_command_plugin_class(
    "DagsterCliPlugin",
    name="dagster",
    version="0.1.0",
    description="Dagster CLI commands (logs, status, backfill, materialize)",
    commands=[dev, logs, status, backfill, materialize],
)
