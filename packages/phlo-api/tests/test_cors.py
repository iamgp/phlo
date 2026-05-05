"""Unit coverage for phlo-api CORS defaults."""

from __future__ import annotations

from fastapi.testclient import TestClient

from phlo_api.main import app


def test_cors_allows_docker_observatory_origin():
    """Docker Observatory can fetch the API directly from the browser."""
    response = TestClient(app).options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3001"
