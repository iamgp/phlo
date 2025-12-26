"""CLI plugin for alerting commands."""

from __future__ import annotations

import click

from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_alerting.cli_alerts import alerts_group


class AlertingCliPlugin(CliCommandPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="alerts",
            version="0.1.0",
            description="Alerting CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        return [alerts_group]
