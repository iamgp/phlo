"""phlo_pandera CLI authorization table."""

from __future__ import annotations

from phlo.cli.authorization import CliSurfaceAdapter, cli_surface_adapter_class

SURFACE_NAME = "phlo-pandera"
FRAMEWORK_TYPE = "cli"
MUTATION_COMMANDS: frozenset[str] = frozenset([])
READ_COMMANDS: frozenset[str] = frozenset(
    [
        "schema.diff",
        "schema.generate",
        "schema.list",
        "schema.show",
        "schema.validate",
        "validate-schema",
        "validate-workflow",
    ]
)
COMMAND_RESOURCE_MAP: dict[str, str] = {}
COMMAND_ACTION_MAP: dict[str, str] = {}

PanderaSurfaceAdapter = cli_surface_adapter_class(
    "PanderaSurfaceAdapter",
    surface_name=SURFACE_NAME,
    mutation_commands=MUTATION_COMMANDS,
    read_commands=READ_COMMANDS,
    command_resource_map=COMMAND_RESOURCE_MAP,
    command_action_map=COMMAND_ACTION_MAP,
    default_action_prefix="pandera",
    default_resource_prefix="pandera",
)


def get_pandera_adapter() -> CliSurfaceAdapter:
    return PanderaSurfaceAdapter.get_instance()
