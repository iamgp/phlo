"""Nessie CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_nessie.cli_branch import branch
from phlo_nessie.cli_catalog import catalog


NessieCliPlugin = cli_command_plugin_class(
    "NessieCliPlugin",
    name="nessie",
    version="0.1.0",
    description="Nessie catalog and branch management commands",
    commands=[catalog, branch],
)
