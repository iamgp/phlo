from __future__ import annotations

from unittest.mock import MagicMock

from phlo.compliance.audit.store import PostgresAuditStore


def test_postgres_audit_store_commits_schema_creation() -> None:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    PostgresAuditStore(conn)

    assert cursor.execute.call_count == 2
    conn.commit.assert_called_once()
    cursor.close.assert_called_once()
