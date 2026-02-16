"""Tests for Trino publishing helpers."""

from __future__ import annotations

from phlo_trino.publishing import (
    _describe_trino_table,
    _is_retryable_introspection_error,
    _trino_table_ref_candidates,
)


class _FakeCursor:
    """Test cursor double that replays canned Trino responses."""

    def __init__(self, trino: "_FakeTrino") -> None:
        """Initialize the fake cursor.

        Args:
            trino: Parent fake Trino client.
        """
        self._trino = trino
        self._rows: list[tuple[object, ...]] = []

    def __enter__(self) -> "_FakeCursor":
        """Return this cursor instance for context-manager usage."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        """Close the context manager.

        Args:
            exc_type: Exception type raised in the context block.
            exc: Exception instance raised in the context block.
            tb: Traceback raised in the context block.
        """
        return None

    def execute(self, query: str) -> None:
        """Execute a fake query and store returned rows.

        Args:
            query: SQL query text used as response lookup key.
        """
        self._trino.queries.append(query)
        response = self._trino.get_response(query)
        if isinstance(response, Exception):
            raise response
        self._rows = list(response or [])

    def fetchall(self) -> list[tuple[object, ...]]:
        """Return rows from the last executed query."""
        return self._rows


class _FakeTrino:
    """Test Trino client double with deterministic query responses."""

    def __init__(
        self,
        responses: dict[str, object],
        sequence_responses: dict[str, list[object]] | None = None,
    ) -> None:
        """Initialize the fake Trino client.

        Args:
            responses: Static response map by SQL query.
            sequence_responses: Queued responses consumed per repeated query.
        """
        self.responses = responses
        self.sequence_responses = {
            query: list(values) for query, values in (sequence_responses or {}).items()
        }
        self.queries: list[str] = []

    def get_response(self, query: str) -> object:
        """Resolve the next configured response for a query.

        Args:
            query: SQL query text.

        Returns:
            The next queued response when configured, otherwise static response.
        """
        queued = self.sequence_responses.get(query)
        if queued:
            return queued.pop(0)
        return self.responses.get(query)

    def cursor(self) -> _FakeCursor:
        """Create a fake cursor bound to this client."""
        return _FakeCursor(self)


def test_trino_table_ref_candidates_include_three_and_two_part_variants() -> None:
    """Ensures table reference candidates include three-part and schema/table forms."""
    refs = _trino_table_ref_candidates("iceberg.raw_marts.posts_mart")

    assert refs == [
        '"iceberg"."raw_marts"."posts_mart"',
        "iceberg.raw_marts.posts_mart",
        '"raw_marts"."posts_mart"',
        "raw_marts.posts_mart",
    ]


def test_describe_trino_table_falls_back_to_schema_table_reference() -> None:
    """Verifies fallback to schema/table reference after catalog-qualified failures."""
    trino = _FakeTrino(
        {
            'DESCRIBE "iceberg"."raw_marts"."posts_mart"': RuntimeError("http 404"),
            'SHOW COLUMNS FROM "iceberg"."raw_marts"."posts_mart"': RuntimeError("http 404"),
            "DESCRIBE iceberg.raw_marts.posts_mart": RuntimeError("http 404"),
            "SHOW COLUMNS FROM iceberg.raw_marts.posts_mart": RuntimeError("http 404"),
            'DESCRIBE "raw_marts"."posts_mart"': [
                ("id", "bigint"),
                ("title", "varchar"),
            ],
        }
    )

    columns, resolved_ref = _describe_trino_table(trino, "iceberg.raw_marts.posts_mart")

    assert resolved_ref == '"raw_marts"."posts_mart"'
    assert columns == [
        ("id", "bigint", '"id"'),
        ("title", "text", '"title"'),
    ]
    assert trino.queries[:3] == [
        'DESCRIBE "iceberg"."raw_marts"."posts_mart"',
        "DESCRIBE iceberg.raw_marts.posts_mart",
        'DESCRIBE "raw_marts"."posts_mart"',
    ]
    assert 'SHOW COLUMNS FROM "iceberg"."raw_marts"."posts_mart"' not in trino.queries
    assert "SHOW COLUMNS FROM iceberg.raw_marts.posts_mart" not in trino.queries


def test_describe_trino_table_retries_after_table_not_found() -> None:
    """Verifies retry occurs when introspection fails with table-not-found error."""
    trino = _FakeTrino(
        responses={},
        sequence_responses={
            'DESCRIBE "iceberg"."raw_marts"."posts_mart"': [
                RuntimeError(
                    "TrinoUserError(type=USER_ERROR, name=TABLE_NOT_FOUND, "
                    'message="table does not exist")'
                ),
                [("id", "bigint"), ("title", "varchar")],
            ]
        },
    )

    columns, resolved_ref = _describe_trino_table(trino, "iceberg.raw_marts.posts_mart")

    assert resolved_ref == '"iceberg"."raw_marts"."posts_mart"'
    assert columns == [
        ("id", "bigint", '"id"'),
        ("title", "text", '"title"'),
    ]
    assert trino.queries.count('DESCRIBE "iceberg"."raw_marts"."posts_mart"') == 2


def test_describe_trino_table_skips_non_retryable_candidate_after_first_failure() -> None:
    """Verifies non-retryable candidates are not retried after first failure."""
    trino = _FakeTrino(
        responses={},
        sequence_responses={
            'DESCRIBE "iceberg"."raw_marts"."posts_mart"': [
                RuntimeError("permission denied"),
                RuntimeError("should not execute"),
            ],
            "DESCRIBE iceberg.raw_marts.posts_mart": [
                RuntimeError(
                    "TrinoUserError(type=USER_ERROR, name=TABLE_NOT_FOUND, "
                    'message="table does not exist")'
                ),
                [("id", "bigint"), ("title", "varchar")],
            ],
        },
    )

    columns, resolved_ref = _describe_trino_table(trino, "iceberg.raw_marts.posts_mart")

    assert resolved_ref == "iceberg.raw_marts.posts_mart"
    assert columns == [
        ("id", "bigint", '"id"'),
        ("title", "text", '"title"'),
    ]
    assert trino.queries.count('DESCRIBE "iceberg"."raw_marts"."posts_mart"') == 1


def test_retryable_introspection_error_uses_structured_fields() -> None:
    """Verifies structured error fields are recognized as retryable."""
    class _StructuredTrinoError(RuntimeError):
        """Structured exception stub mimicking Trino client errors."""

        def __init__(self) -> None:
            """Initialize the structured Trino error stub."""
            super().__init__("opaque server error")
            self.error_name = "TABLE_NOT_FOUND"
            self.error_type = "USER_ERROR"

    assert _is_retryable_introspection_error(_StructuredTrinoError())
