"""Deliberately broken candidate: must fail the query_engine.v1 suite.

Violations: execute() swallows invalid SQL, and preview() returns
positional rows without typed columns. The broken fixture must yield a
failed run, a nonzero exit, and no qualifying tier.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BadPreviewPage:
    columns: list[str]
    column_types: list[int]
    rows: list[tuple[Any, ...]]


class BrokenQueryEngine:
    def __init__(self) -> None:
        self._connection = sqlite3.connect(":memory:")

    def execute(self, sql: str, params: Any = None, schema: str | None = None) -> Any:
        try:
            return self._connection.execute(sql, params or ())
        except sqlite3.Error:
            return None  # violation: errors are swallowed

    def preview(
        self, relation: str, *, limit: int, offset: int = 0, schema: str | None = None
    ) -> BadPreviewPage:
        info = self._connection.execute(f"PRAGMA table_info({relation})").fetchall()
        columns = [str(row[1]) for row in info]
        cursor = self._connection.execute(
            f"SELECT * FROM {relation} LIMIT {int(limit)} OFFSET {int(offset)}"
        )
        return BadPreviewPage(
            columns=columns,
            column_types=[len(name) for name in columns],  # violation: not str
            rows=[tuple(row) for row in cursor.fetchall()],  # violation: not dicts
        )


@dataclass
class QueryEngineSpec:
    name: str
    provider: Any
    metadata: dict[str, Any] = field(default_factory=dict)


class BrokenQueryEngineProvider:
    def get_query_engines(self) -> list[QueryEngineSpec]:
        return [QueryEngineSpec(name="sqlite-fixture-broken", provider=BrokenQueryEngine())]
