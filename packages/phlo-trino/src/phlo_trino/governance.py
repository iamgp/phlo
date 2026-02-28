"""Trino governance backend for access control via SQL grants."""

from __future__ import annotations

from typing import Any

from phlo.capabilities.interfaces import AccessPolicy
from phlo.logging import get_logger
from phlo_trino.resource import TrinoResource

logger = get_logger(__name__)


class TrinoGovernanceBackend:
    """GovernanceBackend implementation using Trino SQL grants."""

    def __init__(self, trino: TrinoResource | None = None) -> None:
        self._trino = trino or TrinoResource()

    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List grants, optionally filtered by table."""
        sql = f"SHOW GRANTS ON TABLE {table_name}" if table_name else "SHOW GRANTS"
        try:
            rows = self._trino.execute(sql)
        except Exception:
            logger.warning(
                "trino_governance_list_policies_failed",
                table_name=table_name,
                exc_info=True,
            )
            return []
        policies: list[dict[str, Any]] = []
        for row in rows:
            policies.append({
                "grantor": row[0] if len(row) > 0 else None,
                "grantee": row[1] if len(row) > 1 else None,
                "catalog": row[2] if len(row) > 2 else None,
                "schema": row[3] if len(row) > 3 else None,
                "table": row[4] if len(row) > 4 else None,
                "privilege": row[5] if len(row) > 5 else None,
                "grantable": row[6] if len(row) > 6 else None,
            })
        return policies

    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply a GRANT or DENY via Trino SQL."""
        action = policy.action.upper()
        if policy.columns:
            logger.warning(
                "trino_governance_column_grants_unsupported", columns=policy.columns
            )

        if policy.effect == "DENY":
            sql = f"DENY {action} ON TABLE {policy.table_pattern} TO {policy.principal}"
        else:
            sql = f"GRANT {action} ON TABLE {policy.table_pattern} TO {policy.principal}"

        logger.info(
            "trino_governance_apply_policy",
            sql=sql,
            principal=policy.principal,
            table=policy.table_pattern,
            action=action,
        )
        self._trino.execute(sql)

    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke a grant. policy_id format: ``ACTION:TABLE:PRINCIPAL``."""
        parts = policy_id.split(":", 2)
        if len(parts) != 3:
            msg = f"policy_id must be 'ACTION:TABLE:PRINCIPAL', got: {policy_id}"
            raise ValueError(msg)
        action, table, principal = parts
        sql = f"REVOKE {action.upper()} ON TABLE {table} FROM {principal}"
        logger.info("trino_governance_revoke_policy", sql=sql, policy_id=policy_id)
        self._trino.execute(sql)

    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check if principal has the specified privilege on a table."""
        policies = self.list_policies(table_name=table_name)
        action_upper = action.upper()
        for policy in policies:
            if (
                policy.get("grantee") == principal
                and policy.get("privilege") == action_upper
            ):
                return True
        return False
