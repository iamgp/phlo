"""Registers the Hasura CLI plugin.

Built declaratively via cli_command_plugin_class(): the module only wires the
hasura command group into the plugin registry under a fixed name and version.
"""

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
