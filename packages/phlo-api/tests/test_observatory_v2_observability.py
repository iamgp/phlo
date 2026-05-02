from phlo_api.observatory_api import v2_observability


def test_load_observability_items_normalizes_backend_links(monkeypatch) -> None:
    monkeypatch.setattr(
        v2_observability,
        "_load_backend_links",
        lambda: [
            {
                "id": "grafana",
                "name": "Grafana",
                "kind": "dashboard",
                "summary": "Dashboards and alerts",
                "health": {"state": "ok", "message": "reachable"},
            },
            {
                "name": "Loki",
                "health": "warning",
            },
            {
                "id": "prometheus",
                "kind": "metrics",
                "summary": "   ",
                "health": {"state": "not-a-state", "message": "ignored"},
            },
        ],
    )

    items = v2_observability.load_observability_items()

    assert [item.id for item in items] == ["grafana", "Loki", "prometheus"]
    assert [item.name for item in items] == ["Grafana", "Loki", "prometheus"]
    assert [item.kind for item in items] == ["dashboard", "observability", "metrics"]
    assert items[0].summary == "Dashboards and alerts"
    assert items[1].summary is None
    assert items[2].summary is None
    assert items[0].health.state == "ok"
    assert items[0].health.message == "reachable"
    assert items[1].health.state == "warning"
    assert items[2].health.state == "unknown"
    assert items[2].health.message is None


def test_load_observability_items_sanitizes_metadata_and_drops_links(monkeypatch) -> None:
    monkeypatch.setattr(
        v2_observability,
        "_load_backend_links",
        lambda: [
            {
                "id": "otel",
                "name": "OpenTelemetry",
                "kind": "traces",
                "metadata": {
                    "tenant": "default",
                    "url": "http://internal.example",
                    "token": "secret",
                    "nested": {"safe": "yes", "endpoint": "http://internal.example"},
                    "native_links": [{"url": "http://internal.example/ui"}],
                    "items": [
                        {"name": "safe"},
                        {"dsn": "postgres://secret", "enabled": True},
                    ],
                },
                "url": "http://internal.example",
                "native_links": [{"url": "http://internal.example/ui"}],
            },
        ],
    )

    items = v2_observability.load_observability_items()

    assert items[0].metadata == {
        "tenant": "default",
        "nested": {"safe": "yes"},
        "items": [{"name": "safe"}, {"enabled": True}],
    }
    assert "url" not in items[0].model_dump()
    assert "native_links" not in items[0].model_dump()


def test_load_observability_items_returns_empty_when_no_backend_links(monkeypatch) -> None:
    monkeypatch.setattr(v2_observability, "_load_backend_links", lambda: [])

    assert v2_observability.load_observability_items() == []


def test_load_observability_items_ignores_bad_backend_shapes(monkeypatch) -> None:
    monkeypatch.setattr(
        v2_observability,
        "_load_backend_links",
        lambda: [{"id": "loki", "name": "Loki"}, "bad"],
    )

    items = v2_observability.load_observability_items()

    assert [item.id for item in items] == ["loki"]

    monkeypatch.setattr(v2_observability, "_load_backend_links", lambda: None)
    assert v2_observability.load_observability_items() == []

    def raise_error() -> list[dict[str, object]]:
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(v2_observability, "_load_backend_links", raise_error)
    assert v2_observability.load_observability_items() == []
