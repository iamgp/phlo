"""Tests for Nessie catalog scanner capability resolution."""

from __future__ import annotations

from phlo_nessie.catalog_scanner import NessieTableScanner


class _QueryEngine:
    def __init__(self, rows):
        self.rows = rows
        self.queries: list[str] = []

    def execute(self, sql: str, params=None, schema=None):
        self.queries.append(sql)
        return self.rows


def test_list_namespaces_uses_query_engine_capability(monkeypatch) -> None:
    """Fallback namespace scans should resolve the query engine via capabilities."""
    engine = _QueryEngine([("raw",), ("curated",)])
    monkeypatch.setattr(
        "phlo_nessie.catalog_scanner.resolve_capability",
        lambda capability_type, name: (
            type("Resolution", (), {"provider": engine})()
            if capability_type == "query_engine" and name == "trino"
            else None
        ),
    )
    scanner = NessieTableScanner("http://nessie.example")

    namespaces = scanner._list_namespaces_via_trino()

    assert namespaces == [{"namespace": ["raw"]}, {"namespace": ["curated"]}]
    assert engine.queries == ["SHOW SCHEMAS"]


def test_get_query_engine_returns_none_when_capability_missing(monkeypatch) -> None:
    """Fallback paths should tolerate missing query engine providers."""
    monkeypatch.setattr(
        "phlo_nessie.catalog_scanner.resolve_capability", lambda *_args, **_kwargs: None
    )
    scanner = NessieTableScanner("http://nessie.example")

    assert scanner._get_query_engine() is None
