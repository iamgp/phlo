"""Pandera regulated surface adapter.

This module provides the regulated surface adapter for the Pandera CLI commands,
declaring which operations are mutations vs reads.

Pandera CLI commands are all read-only operations (schema inspection, validation,
generation) that do not modify system state.

Principal resolution strategy:
- Inherits from CLI principal resolver (see phlo.cli.authorization)

Read commands (no authorization required):
- schema.list: List available Pandera schemas
- schema.show: Show schema details
- schema.diff: Compare schema versions
- schema.validate: Validate schema file syntax
- schema.generate: Generate schema from DLT source (dry-run or writes schema file)
- validate-schema: Validate a Pandera schema file
- validate-workflow: Validate a workflow asset file

Mutation commands: none - all Pandera CLI commands are reads.
"""

from __future__ import annotations

from typing import Any

from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)

SURFACE_NAME = "phlo-pandera"
FRAMEWORK_TYPE = "cli"

READ_COMMANDS: frozenset[str] = frozenset(
    {
        "schema.list",
        "schema.show",
        "schema.diff",
        "schema.validate",
        "schema.generate",
        "validate-schema",
        "validate-workflow",
    }
)


class PanderaSurfaceAdapter:
    """Regulated surface adapter for Phlo Pandera CLI.

    All Pandera CLI commands are read-only operations that inspect
    schemas and validate code without modifying system state.
    """

    _instance: "PanderaSurfaceAdapter | None" = None

    def __init__(self) -> None:
        pass

    @classmethod
    def get_instance(cls) -> "PanderaSurfaceAdapter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def surface_name(self) -> str:
        return SURFACE_NAME

    @property
    def framework_type(self) -> str:
        return FRAMEWORK_TYPE

    def list_operations(self) -> list[SurfaceOperation]:
        return []

    def is_active(self, runtime: Any) -> bool:
        return True

    def install(self, runtime: Any) -> None:
        pass

    def check_command_authorization(self, command: str) -> EnforcementResult:
        if command in READ_COMMANDS:
            return EnforcementResult.allow()

        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command}' is not classified for Pandera CLI",
        )


def get_pandera_adapter() -> PanderaSurfaceAdapter:
    return PanderaSurfaceAdapter.get_instance()
