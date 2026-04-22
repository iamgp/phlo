"""CLI regulated surface adapter for Nessie.

This module provides the regulated surface adapter for the Nessie CLI,
declaring mutation commands that require authorization and enforcing
through core enforcement.

Commands:
- branch list: List branches (read)
- branch create: Create a branch (mutation)
- branch delete: Delete a branch (mutation)
- branch merge: Merge branches (mutation)
- branch diff: Show branch differences (read)
- catalog tables: List catalog tables (read)
- catalog describe: Describe table metadata (read)
- catalog history: Show table history (read)

Resource/Action mapping:
- catalog.manage: Branch management (create, delete, merge)
- catalog.read: Catalog queries (list, diff, tables, describe, history)
"""

from __future__ import annotations

import os
import threading
from typing import Any

from phlo.cli.authorization import CliPrincipalResolver
from phlo.logging import get_logger
from phlo.security.adapters import (
    EnforcementResult,
    SurfaceOperation,
)
from phlo.security.enforcement import enforce

logger = get_logger(__name__)

SURFACE_NAME = "phlo-nessie-cli"
FRAMEWORK_TYPE = "cli"

MUTATION_COMMANDS: frozenset[str] = frozenset(
    {
        "branch.create",
        "branch.delete",
        "branch.merge",
    }
)

READ_COMMANDS: frozenset[str] = frozenset(
    {
        "branch.list",
        "branch.diff",
        "catalog.tables",
        "catalog.describe",
        "catalog.history",
    }
)

COMMAND_RESOURCE_MAP: dict[str, str] = {
    "branch.create": "catalog",
    "branch.delete": "catalog",
    "branch.merge": "catalog",
    "branch.list": "catalog",
    "branch.diff": "catalog",
    "catalog.tables": "catalog",
    "catalog.describe": "catalog",
    "catalog.history": "catalog",
}

COMMAND_ACTION_MAP: dict[str, str] = {
    "branch.create": "catalog.manage",
    "branch.delete": "catalog.manage",
    "branch.merge": "catalog.manage",
    "branch.list": "catalog.read",
    "branch.diff": "catalog.read",
    "catalog.tables": "catalog.read",
    "catalog.describe": "catalog.read",
    "catalog.history": "catalog.read",
}


class NessieCliSurfaceAdapter:
    """Regulated surface adapter for Nessie CLI."""

    _instance: NessieCliSurfaceAdapter | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._resolver = CliPrincipalResolver()

    @classmethod
    def get_instance(cls) -> NessieCliSurfaceAdapter:
        if cls._instance is None:
            with cls._lock:
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
            resource_type = COMMAND_RESOURCE_MAP.get(command, "catalog")
            action = COMMAND_ACTION_MAP.get(command, "catalog.manage")
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
        """Enforce authorization for a mutation command."""
        if command not in MUTATION_COMMANDS:
            return EnforcementResult.allow()

        action = COMMAND_ACTION_MAP.get(command, "catalog.manage")
        resource_type = COMMAND_RESOURCE_MAP.get(command, "catalog")
        resource_id_final = resource_id or f"nessie:{command}"

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
            "nessie_cli_mutation_enforcement_result",
            command=command,
            action=action,
            result=result.variant,
            subject=principal.subject,
        )

        return result

    def check_command_authorization(self, command_path: str) -> EnforcementResult:
        """Check if a command is authorized to run."""
        if command_path in READ_COMMANDS:
            return EnforcementResult.allow()

        if command_path in MUTATION_COMMANDS:
            return self.enforce_mutation(command_path)

        logger.warning(
            "nessie_cli_unknown_command_classification",
            command=command_path,
        )
        return EnforcementResult.deny(
            reason_code="unknown_command",
            explanation=f"Command '{command_path}' is not classified as read or mutation",
        )


def get_nessie_cli_adapter() -> NessieCliSurfaceAdapter:
    """Get the singleton Nessie CLI surface adapter."""
    return NessieCliSurfaceAdapter.get_instance()
