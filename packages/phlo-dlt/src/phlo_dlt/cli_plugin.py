"""CLI plugin for DLT workflow scaffolding."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dlt.cli_workflow import workflow_group


class DltCliPlugin(CliCommandPlugin):
    """Expose DLT CLI command groups to the Phlo plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for CLI command discovery.

        Returns:
            PluginMetadata: Static metadata for the DLT CLI plugin.
        """
        return PluginMetadata(
            name="dlt",
            version="0.1.0",
            description="Workflow scaffolding commands for DLT ingestion",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            list[click.Command]: Registered top-level DLT CLI command groups.
        """
        return [workflow_group]
