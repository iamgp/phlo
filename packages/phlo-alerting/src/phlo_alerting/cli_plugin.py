"""Alerting CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_alerting.cli_alerts import alerts_group


AlertingCliPlugin = cli_command_plugin_class(
    "AlertingCliPlugin",
    name="alerts",
    version="0.1.0",
    description="Alerting CLI commands",
    commands=[alerts_group],
)
