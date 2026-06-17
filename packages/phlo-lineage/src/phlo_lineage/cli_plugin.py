"""Lineage CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class
from phlo_lineage.cli_lineage import lineage_group


LineageCliPlugin = cli_command_plugin_class(
    "LineageCliPlugin",
    name="lineage",
    version="0.1.0",
    description="Lineage CLI commands",
    commands=[lineage_group],
)
