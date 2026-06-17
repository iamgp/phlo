"""Dlt CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_dlt.cli_workflow import workflow_group


DltCliPlugin = cli_command_plugin_class(
    "DltCliPlugin",
    name="dlt",
    version="0.1.0",
    description="Workflow scaffolding commands for DLT ingestion",
    commands=[workflow_group],
)
