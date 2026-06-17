"""Clickstack CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class

from phlo_clickstack.cli import clickstack_group


ClickStackCliPlugin = cli_command_plugin_class(
    "ClickStackCliPlugin",
    name="clickstack",
    version="0.1.0",
    description="CLI commands for ClickStack query access",
    commands=[clickstack_group],
)
