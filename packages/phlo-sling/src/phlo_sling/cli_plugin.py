"""Sling CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_sling.cli_commands import sling_group


SlingCliPlugin = cli_command_plugin_class(
    "SlingCliPlugin",
    name="sling",
    version="0.1.0",
    description="Sling replication CLI commands for Phlo",
    commands=[sling_group],
)
