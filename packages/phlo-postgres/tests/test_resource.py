from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from phlo_postgres.resource import PostgresResource


def _resource() -> PostgresResource:
    """Build a Postgres resource configured for local unit tests.

    Returns:
        Configured `PostgresResource` instance.
    """
    return PostgresResource(
        host="localhost",
        port=5432,
        user="phlo",
        password="secret",
        database="phlo",
    )


def test_context_manager_rolls_back_and_closes_on_error() -> None:
    """Verify context manager rolls back and closes connection on exception."""
    connection = MagicMock()
    connection.closed = 0

    with patch("phlo_postgres.resource.psycopg2.connect", return_value=connection):
        with pytest.raises(RuntimeError, match="boom"):
            with _resource():
                raise RuntimeError("boom")

    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_transactional_cursor_commits_on_success() -> None:
    """Verify transactional cursor commits and closes cursor on success."""
    connection = MagicMock()
    connection.closed = 0
    cursor = MagicMock()
    connection.cursor.return_value = cursor

    with patch("phlo_postgres.resource.psycopg2.connect", return_value=connection):
        resource = _resource()
        with resource.transactional_cursor() as current_cursor:
            assert current_cursor is cursor
            current_cursor.execute("SELECT 1")

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()


def test_transactional_cursor_rolls_back_on_error() -> None:
    """Verify transactional cursor rolls back and closes cursor on failure."""
    connection = MagicMock()
    connection.closed = 0
    cursor = MagicMock()
    connection.cursor.return_value = cursor

    with patch("phlo_postgres.resource.psycopg2.connect", return_value=connection):
        resource = _resource()
        with pytest.raises(ValueError, match="fail"):
            with resource.transactional_cursor():
                raise ValueError("fail")

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
