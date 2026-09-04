"""Independently packaged SQLite query-engine conformance fixture.

Deliberately outside ``packages/*``, the registry, and the support
profiles: this is a candidate artifact for the conformance runner, not a
first-party or supported package. It implements the ``query_engine.v1``
contract structurally (no Phlo import) so it can execute inside the
disposable worker with nothing but this wheel installed.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreviewPage:
    columns: list[str]
    column_types: list[str]
    rows: list[dict[str, Any]]


class SQLiteQueryEngine:
    """QueryEngine-protocol implementation over an in-memory SQLite database."""

    def __init__(self) -> None:
        self._connection = sqlite3.connect(":memory:")

    def execute(self, sql: str, params: Any = None, schema: str | None = None) -> Any:
        return self._connection.execute(sql, params or ())

    def preview(
        self, relation: str, *, limit: int, offset: int = 0, schema: str | None = None
    ) -> PreviewPage:
        info = self._connection.execute(f"PRAGMA table_info({relation})").fetchall()
        columns = [str(row[1]) for row in info]
        column_types = [str(row[2]) or "TEXT" for row in info]
        cursor = self._connection.execute(
            f"SELECT * FROM {relation} LIMIT ? OFFSET ?", (limit, offset)
        )
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        return PreviewPage(columns=columns, column_types=column_types, rows=rows)


@dataclass
class QueryEngineSpec:
    name: str
    provider: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class SQLiteQueryEngineProvider:
    """Candidate-owned resource provider exposing one query-engine spec."""

    def get_query_engines(self) -> list[QueryEngineSpec]:
        return [
            QueryEngineSpec(
                name="sqlite-fixture",
                provider=SQLiteQueryEngine(),
                metadata={"service_type": "SQLiteFixture"},
            )
        ]
