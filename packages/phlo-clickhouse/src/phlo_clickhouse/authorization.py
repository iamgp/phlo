"""phlo_clickhouse CLI authorization table."""

from __future__ import annotations

from phlo.cli.authorization import cli_surface_adapter_class

SURFACE_NAME = "phlo-clickhouse"
FRAMEWORK_TYPE = "cli"
MUTATION_COMMANDS: frozenset[str] = frozenset(["clickhouse.query"])
READ_COMMANDS: frozenset[str] = frozenset(["clickhouse.status"])
COMMAND_RESOURCE_MAP: dict[str, str] = {"clickhouse.query": "dataset"}
COMMAND_ACTION_MAP: dict[str, str] = {"clickhouse.query": "dataset.write"}

ClickHouseSurfaceAdapter = cli_surface_adapter_class(
    "ClickHouseSurfaceAdapter",
    surface_name=SURFACE_NAME,
    mutation_commands=MUTATION_COMMANDS,
    read_commands=READ_COMMANDS,
    command_resource_map=COMMAND_RESOURCE_MAP,
    command_action_map=COMMAND_ACTION_MAP,
    default_action_prefix="clickhouse",
    default_resource_prefix="clickhouse",
)


def get_adapter() -> ClickHouseSurfaceAdapter:
    return ClickHouseSurfaceAdapter.get_instance()
