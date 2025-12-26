"""CLI plugin for metrics commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_metrics.cli import metrics_group


class MetricsCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics",
            version="0.1.0",
            description="Metrics summary and export commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [metrics_group]
