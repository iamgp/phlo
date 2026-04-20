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


def test_postgres_audit_store_rolls_back_failed_schema_creation() -> None:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.execute.side_effect = RuntimeError("ddl failed")

    try:
        PostgresAuditStore(conn)
    except RuntimeError as exc:
        assert str(exc) == "ddl failed"
    else:
        raise AssertionError("Expected schema creation failure")

    conn.rollback.assert_called_once()
    cursor.close.assert_called_once()
    conn.commit.assert_not_called()


def test_postgres_audit_store_rolls_back_failed_append() -> None:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    store = PostgresAuditStore(conn)
    conn.reset_mock()
    cursor.reset_mock()
    cursor.execute.side_effect = RuntimeError("insert failed")

    record = MagicMock()
    record.event.to_dict.return_value = {"event_id": "evt-1"}
    record.event.surface = "phlo-api"
    record.sequence_number = 1
    record.sealed_at = "2026-04-20T00:00:00Z"
    record.previous_hash = "prev"
    record.record_hash = "hash"

    try:
        store.append(record)
    except RuntimeError as exc:
        assert str(exc) == "insert failed"
    else:
        raise AssertionError("Expected append failure")

    conn.rollback.assert_called_once()
    cursor.close.assert_called_once()
    conn.commit.assert_not_called()
