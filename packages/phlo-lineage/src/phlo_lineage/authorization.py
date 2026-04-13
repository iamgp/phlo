"""Lineage regulated surface adapter.

This module provides the regulated surface adapter for the lineage CLI commands,
declaring which operations are mutations vs reads.

Principal resolution strategy:
- Inherits from CLI principal resolver (see phlo.cli.authorization)

Read commands (no authorization required):
- lineage.show: Display ASCII tree lineage visualization
- lineage.export: Export to DOT, Mermaid, or JSON formats
- lineage.impact: Analyze downstream impact of changes
- lineage.status: Display graph statistics
- lineage.column.upstream: Query upstream column lineage
- lineage.column.downstream: Query downstream column lineage

Mutation commands (require authorization):
- lineage.column.import-dbt: Import column lineage from dbt manifest (writes to lineage store)
"""

from __future__ import annotations

import os
from typing import Any

from phlo.logging import get_logger
from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)
from phlo.security.enforcement import enforce

logger = get_logger(__name__)

SURFACE_NAME = "phlo-lineage"
FRAMEWORK_TYPE = "cli"

MUTATION_COMMANDS: frozenset[str] = frozenset(
    {
        "lineage.column.import-dbt",
    }
)

READ_COMMANDS: frozenset[str] = frozenset(
    {
        "lineage.show",
        "lineage.export",
        "lineage.impact",
        "lineage.status",
        "lineage.column.upstream",
        "lineage.column.downstream",
    }
)

COMMAND_RESOURCE_MAP: dict[str, str] = {
    "lineage.column.import-dbt": "lineage_store",
}

COMMAND_ACTION_MAP: dict[str, str] = {
    "lineage.column.import-dbt": "lineage.import",
}


class LineageCliPrincipalResolver:
    """Resolves CLI principal from execution environment.

    Delegates to the main CLI principal resolver for consistency.
    """

    @staticmethod
    def resolve():
        from phlo.cli.authorization import CliPrincipalResolver

        return CliPrincipalResolver().resolve()


class LineageSurfaceAdapter:
    """Regulated surface adapter for Phlo lineage CLI.

    Declares mutation commands and enforces authorization through core
    enforcement for privileged operations.
    """

    _instance: "LineageSurfaceAdapter | None" = None

    def __init__(self) -> None:
        self._resolver = LineageCliPrincipalResolver()

    @classmethod
    def get_instance(cls) -> "LineageSurfaceAdapter":
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
        operations: list[SurfaceOperation] = []
        for command in MUTATION_COMMANDS:
            resource_type = COMMAND_RESOURCE_MAP.get(command, "lineage")
            action = COMMAND_ACTION_MAP.get(command, f"lineage.{command}")
            operations.append(
                SurfaceOperation(
                    action=action,
                    resource_type=resource_type,
                    operation_name=command,
                    resource_id_strategy=None,
                    framework_metadata={"command": command},
                )
            )
        return operations

    def is_active(self, runtime: Any) -> bool:
        return True

    def install(self, runtime: Any) -> None:
        pass

    def enforce_mutation(self, command: str, resource_id: str | None = None) -> EnforcementResult:
        if command not in MUTATION_COMMANDS:
            return EnforcementResult.allow()

        action = COMMAND_ACTION_MAP.get(command, f"lineage.{command}")
        resource_type = COMMAND_RESOURCE_MAP.get(command, "lineage")
        resource_id_final = resource_id or f"lineage:{command}"

        principal = self._resolver.resolve()

        from phlo.capabilities.interfaces import ResourceRef

        resource = ResourceRef(
            resource_type=resource_type,
            resource_id=resource_id_final,
        )

        request_id = os.environ.get("PHLO_REQUEST_ID")

        result = enforce(
            principal=principal,
            action=action,
            resource=resource,
            context=None,
            request_id=request_id,
            surface=SURFACE_NAME,
        )

        logger.debug(
            "lineage_mutation_enforcement_result",
            command=command,
            action=action,
            result=result.variant,
            subject=principal.subject,
        )

        return result

    def check_command_authorization(self, command_path: str) -> EnforcementResult:
        if command_path in READ_COMMANDS:
            return EnforcementResult.allow()

        if command_path in MUTATION_COMMANDS:
            return self.enforce_mutation(command_path)

        logger.warning(
            "lineage_unknown_command_classification",
            command=command_path,
        )
        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command_path}' is not classified as read or mutation",
        )


def get_lineage_adapter() -> LineageSurfaceAdapter:
    return LineageSurfaceAdapter.get_instance()
