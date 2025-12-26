"""CLI plugin for quality and schema commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_quality.cli_schema import schema
from phlo_quality.cli_validate import validate_schema, validate_workflow


class QualityCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="quality",
            version="0.1.0",
            description="Quality and schema CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [schema, validate_schema, validate_workflow]
