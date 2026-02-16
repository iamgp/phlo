"""CLI plugin for quality and schema commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_quality.cli_schema import schema
from phlo_quality.cli_validate import validate_schema, validate_workflow


class QualityCliPlugin(CliCommandPlugin):
    """Register quality validation and schema commands with the CLI."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for quality CLI commands.

        Returns:
            PluginMetadata: Metadata used for plugin discovery and display.
        """
        return PluginMetadata(
            name="quality",
            version="0.1.0",
            description="Quality and schema CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Quality command set registered by the plugin.
        """
        return [schema, validate_schema, validate_workflow]
