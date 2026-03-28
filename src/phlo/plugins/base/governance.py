"""Governance plugin classes.

This module defines plugin types for access control, data masking,
and policy enforcement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from phlo.capabilities.interfaces import AccessPolicy
from phlo.plugins.base.plugin import Plugin


class GovernancePlugin(Plugin, ABC):
    """Base class for governance plugins.

    Governance plugins provide access control, data masking, row-level
    security, and policy enforcement for lakehouse tables.

    Example:
        ```python
        class TrinoRBACPlugin(GovernancePlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="trino-rbac",
                    version="1.0.0",
                    description="Trino RBAC governance",
                )

            def list_policies(self, table_name=None):
                return self._fetch_policies(table_name)

            def apply_policy(self, policy):
                self._execute_grant(policy)

            def revoke_policy(self, policy_id):
                self._execute_revoke(policy_id)

            def check_access(self, principal, table_name, action):
                return self._query_access(principal, table_name, action)
        ```

    """

    @abstractmethod
    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List access policies, optionally filtered by table."""
        raise NotImplementedError

    @abstractmethod
    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply an access policy."""
        raise NotImplementedError

    @abstractmethod
    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke an access policy by identifier."""
        raise NotImplementedError

    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check whether a principal has access. Returns True by default."""
        return True

    def get_masking_rules(self, *, table_name: str) -> list[dict[str, Any]]:
        """Return column masking rules for a table."""
        return []

    def get_row_filters(self, *, table_name: str) -> list[dict[str, Any]]:
        """Return row-level filter rules for a table."""
        return []

    def get_data_classifications(self) -> Iterable[dict[str, Any]]:
        """Return data classification tags (PII, sensitive, public, etc.)."""
        return []
