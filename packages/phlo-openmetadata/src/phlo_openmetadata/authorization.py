"""phlo_openmetadata CLI authorization table."""

from __future__ import annotations

from phlo.cli.authorization import cli_surface_adapter_class

SURFACE_NAME = "phlo-openmetadata"
FRAMEWORK_TYPE = "cli"
MUTATION_COMMANDS: frozenset[str] = frozenset(["openmetadata.sync"])
READ_COMMANDS: frozenset[str] = frozenset(["openmetadata.health"])
COMMAND_RESOURCE_MAP: dict[str, str] = {"openmetadata.sync": "metadata_catalog"}
COMMAND_ACTION_MAP: dict[str, str] = {"openmetadata.sync": "metadata.sync"}

OpenMetadataSurfaceAdapter = cli_surface_adapter_class(
    "OpenMetadataSurfaceAdapter",
    surface_name=SURFACE_NAME,
    mutation_commands=MUTATION_COMMANDS,
    read_commands=READ_COMMANDS,
    command_resource_map=COMMAND_RESOURCE_MAP,
    command_action_map=COMMAND_ACTION_MAP,
    default_action_prefix="openmetadata",
    default_resource_prefix="openmetadata",
)


def get_openmetadata_adapter() -> OpenMetadataSurfaceAdapter:
    return OpenMetadataSurfaceAdapter.get_instance()
