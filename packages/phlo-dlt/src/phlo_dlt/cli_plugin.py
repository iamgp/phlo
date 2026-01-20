"""CLI plugin for DLT workflow scaffolding."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dlt.cli_workflow import workflow_group


class DltCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="Workflow scaffolding commands for DLT ingestion",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [workflow_group]
