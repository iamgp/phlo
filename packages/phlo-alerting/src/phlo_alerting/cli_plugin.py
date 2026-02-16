"""CLI plugin for alerting commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_alerting.cli_alerts import alerts_group


class AlertingCliPlugin(CliCommandPlugin):
    """Expose alerting commands to the Phlo CLI plugin system."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin identity metadata for discovery.

        Returns:
            Plugin metadata for alerting commands.
        """
        return PluginMetadata(
            name="alerts",
            version="0.1.0",
            description="Alerting CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands provided by the alerting plugin.

        Returns:
            Ordered list of alerting Click commands.
        """
        return [alerts_group]
