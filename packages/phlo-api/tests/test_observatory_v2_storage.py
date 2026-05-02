"""Tests for Observatory v2 storage surface normalization."""

from __future__ import annotations

import pytest

from phlo_api.observatory_api import v2_storage


def test_load_storage_items_normalizes_backend_mappings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        v2_storage,
        "_load_backend_items",
        lambda: [
            {
                "id": 123,
                "name": "Object Store",
                "kind": "s3",
                "summary": "Primary lakehouse object storage",
                "health": {"state": "ok", "message": "reachable"},
                "metadata": {"bucket_count": 3},
            },
            {
                "name": "Warehouse Volume",
            },
        ],
    )

    items = v2_storage.load_storage_items()

    assert items[0].id == "123"
    assert items[0].name == "Object Store"
    assert items[0].kind == "s3"
    assert items[0].summary == "Primary lakehouse object storage"
    assert items[0].health.state == "ok"
    assert items[0].health.message == "reachable"
    assert items[0].metadata == {"bucket_count": 3}

    assert items[1].id == "storage-2"
    assert items[1].name == "Warehouse Volume"
    assert items[1].kind == "storage"
    assert items[1].summary is None
    assert items[1].health.state == "unknown"
    assert items[1].metadata == {}


def test_load_storage_items_sanitizes_metadata_and_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2_storage,
        "_load_backend_items",
        lambda: [
            {
                "id": "minio",
                "name": "MinIO",
                "kind": "object_storage",
                "summary": "",
                "health": "warning",
                "metadata": {
                    "region": "local",
                    "endpoint": "http://minio:9000",
                    "native_links": [{"label": "MinIO", "url": "http://minio:9001"}],
                    "nested": {"token": "secret", "tier": "bronze"},
                    "values": ["plain", "postgres://user:pass@host/db"],
                },
                "url": "http://minio:9001",
                "native_links": [{"url": "http://minio:9001"}],
            }
        ],
    )

    item = v2_storage.load_storage_items()[0]

    assert item.summary is None
    assert item.health.state == "warning"
    assert item.metadata == {
        "region": "local",
        "nested": {"tier": "bronze"},
        "values": ["plain"],
    }


def test_load_storage_items_returns_empty_list_when_backend_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(v2_storage, "_load_backend_items", lambda: [])

    assert v2_storage.load_storage_items() == []


def test_load_storage_items_ignores_bad_backend_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2_storage,
        "_load_backend_items",
        lambda: [{"id": "minio", "name": "MinIO"}, "bad"],
    )

    items = v2_storage.load_storage_items()

    assert [item.id for item in items] == ["minio"]

    monkeypatch.setattr(v2_storage, "_load_backend_items", lambda: None)
    assert v2_storage.load_storage_items() == []

    def raise_error() -> list[dict[str, object]]:
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(v2_storage, "_load_backend_items", raise_error)
    assert v2_storage.load_storage_items() == []
