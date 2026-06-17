"""Clickhouse CLI plugin registration."""

from __future__ import annotations


from phlo.plugins.base import cli_command_plugin_class

from phlo_clickhouse.cli import clickhouse_group


ClickHouseCliPlugin = cli_command_plugin_class(
    "ClickHouseCliPlugin",
    name="clickhouse",
    version="0.1.0",
    description="CLI commands for ClickHouse data plane access",
    commands=[clickhouse_group],
)
