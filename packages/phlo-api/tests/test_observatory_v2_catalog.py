"""Tests for Observatory v2 catalog surface normalization."""

from __future__ import annotations

import pytest

from phlo_api.observatory_api import v2_catalog


def test_load_catalog_items_normalizes_backend_mappings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2_catalog,
        "_load_backend_items",
        lambda: [
            {
                "id": 42,
                "name": "main",
                "kind": "nessie",
                "summary": "Default catalog",
                "health": {"state": "ok", "message": "reachable"},
            },
            {
                "name": "warehouse",
                "health": "warning",
            },
        ],
    )

    items = v2_catalog.load_catalog_items()

    assert len(items) == 2
    assert items[0].id == "42"
    assert items[0].name == "main"
    assert items[0].kind == "nessie"
    assert items[0].summary == "Default catalog"
    assert items[0].health.state == "ok"
    assert items[0].health.message == "reachable"
    assert items[1].id == "warehouse"
    assert items[1].name == "warehouse"
    assert items[1].kind == "catalog"
    assert items[1].summary is None
    assert items[1].health.state == "warning"
    assert items[1].health.message is None


def test_load_catalog_items_sanitizes_metadata_and_drops_native_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2_catalog,
        "_load_backend_items",
        lambda: [
            {
                "id": "catalog-a",
                "metadata": {
                    "branch": "main",
                    "endpoint": "https://nessie.example.internal",
                    "native_links": [{"label": "Nessie", "url": "https://nessie.example.internal"}],
                    "token": "secret",
                    "nested": {
                        "team": "platform",
                        "connection_url": "postgres://user:password@host/db",
                    },
                },
                "url": "https://nessie.example.internal/ui",
                "native_links": [{"label": "Nessie", "url": "https://nessie.example.internal"}],
            }
        ],
    )

    item = v2_catalog.load_catalog_items()[0]

    assert item.metadata == {
        "branch": "main",
        "nested": {"team": "platform"},
    }
    assert not hasattr(item, "url")
    assert not hasattr(item, "native_links")


def test_load_catalog_items_returns_empty_list_when_backend_has_no_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(v2_catalog, "_load_backend_items", lambda: [])

    assert v2_catalog.load_catalog_items() == []


def test_load_catalog_items_ignores_bad_backend_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2_catalog,
        "_load_backend_items",
        lambda: [{"id": "nessie", "name": "Nessie"}, "bad"],
    )

    items = v2_catalog.load_catalog_items()

    assert [item.id for item in items] == ["nessie"]

    monkeypatch.setattr(v2_catalog, "_load_backend_items", lambda: None)
    assert v2_catalog.load_catalog_items() == []

    def raise_error() -> list[dict[str, object]]:
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(v2_catalog, "_load_backend_items", raise_error)
    assert v2_catalog.load_catalog_items() == []
