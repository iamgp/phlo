"""CLI plugin for metrics commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata


class MetricsCliPlugin(CliCommandPlugin):
    """Register metrics CLI commands with the plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata for metrics commands.

        Returns:
            PluginMetadata: Metadata used for plugin discovery and display.
        """
        return PluginMetadata(
            name="metrics",
            version="0.1.0",
            description="Metrics summary and export commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands exposed by this plugin.

        Returns:
            list[click.Command]: Registered metrics command group.
        """
        from phlo_metrics.cli import metrics_group

        return [metrics_group]
