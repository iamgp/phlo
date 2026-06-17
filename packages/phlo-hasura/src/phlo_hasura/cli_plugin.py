"""Hasura CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_hasura.cli import hasura


HasuraCliPlugin = cli_command_plugin_class(
    "HasuraCliPlugin",
    name="hasura",
    version="0.1.0",
    description="Hasura CLI commands for metadata management",
    commands=[hasura],
)
