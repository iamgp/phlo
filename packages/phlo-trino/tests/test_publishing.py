"""Tests for Trino publishing helpers."""

from __future__ import annotations

from phlo_trino.publishing import (
    _describe_trino_table,
    _is_retryable_introspection_error,
    _trino_table_ref_candidates,
)


class _FakeCursor:
    def __init__(self, trino: "_FakeTrino") -> None:
        self._trino = trino
        self._rows: list[tuple[object, ...]] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def execute(self, query: str) -> None:
        self._trino.queries.append(query)
        response = self._trino.get_response(query)
        if isinstance(response, Exception):
            raise response
        self._rows = list(response or [])

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._rows


class _FakeTrino:
    def __init__(
        self,
        responses: dict[str, object],
        sequence_responses: dict[str, list[object]] | None = None,
    ) -> None:
        self.responses = responses
        self.sequence_responses = {
            query: list(values) for query, values in (sequence_responses or {}).items()
        }
        self.queries: list[str] = []

    def get_response(self, query: str) -> object:
        queued = self.sequence_responses.get(query)
        if queued:
            return queued.pop(0)
        return self.responses.get(query)

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)


def test_trino_table_ref_candidates_include_three_and_two_part_variants() -> None:
    refs = _trino_table_ref_candidates("iceberg.raw_marts.posts_mart")

    assert refs == [
        '"iceberg"."raw_marts"."posts_mart"',
        "iceberg.raw_marts.posts_mart",
        '"raw_marts"."posts_mart"',
        "raw_marts.posts_mart",
    ]


def test_describe_trino_table_falls_back_to_schema_table_reference() -> None:
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
    class _StructuredTrinoError(RuntimeError):
        def __init__(self) -> None:
            super().__init__("opaque server error")
            self.error_name = "TABLE_NOT_FOUND"
            self.error_type = "USER_ERROR"

    assert _is_retryable_introspection_error(_StructuredTrinoError())
