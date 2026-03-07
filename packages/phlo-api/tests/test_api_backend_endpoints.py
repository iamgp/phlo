"""Tests for capability-backed API backend endpoints."""

from __future__ import annotations


def test_api_backends_endpoint_returns_capability_payload(monkeypatch) -> None:
    """The API should expose capability-backed backend discovery."""
    from fastapi.testclient import TestClient
    from phlo_api.main import app
    import phlo_api.main as main_module

    payload = [
        {
            "name": "hasura",
            "healthy": True,
            "metadata": {"backend_kind": "graphql"},
            "description": {"service_name": "hasura"},
        }
    ]
    monkeypatch.setattr(main_module, "_list_api_backends", lambda: payload)

    client = TestClient(app)
    response = client.get("/api/backends")

    assert response.status_code == 200
    assert response.json() == payload


def test_api_backend_endpoint_returns_404_for_unknown_backend(monkeypatch) -> None:
    """Unknown API backend names should return 404."""
    from fastapi.testclient import TestClient
    from phlo_api.main import app
    import phlo_api.main as main_module

    monkeypatch.setattr(main_module, "_get_api_backend", lambda _name: None)

    client = TestClient(app)
    response = client.get("/api/backends/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "API backend not found: missing"
