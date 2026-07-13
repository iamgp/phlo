"""Mechanical coverage and access-matrix tests for the mandatory API boundary."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from phlo.capabilities.interfaces import AuthPrincipal, AuthorizationDecision, Principal
from phlo_api.main import app
from phlo_api.security_manifest import (
    GRAPHQL_OPERATION_MANIFEST,
    HTTP_ROUTE_MANIFEST,
    OperationSpec,
    WEBSOCKET_OPERATION_MANIFEST,
    resolve_resource,
    validate_manifest,
    validate_operation_registry,
)


class _Backend:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str, str, str]] = []
        self.contexts = []

    def explain_decision(self, principal, action, resource, context=None):  # noqa: ANN001
        self.calls.append((principal.subject, action, resource.resource_id))
        self.contexts.append(context)
        return AuthorizationDecision(
            allowed=self.allowed,
            reason_code="explicit_allow" if self.allowed else "default_deny",
            policy_id="test-policy" if self.allowed else None,
            explanation="test decision",
        )


def _principal(subject: str = "viewer") -> tuple[AuthPrincipal, Principal]:
    auth = AuthPrincipal(subject=subject, principal_type="user", groups=())
    canonical = Principal(subject=subject, principal_type="user", roles=(subject,))
    return auth, canonical


def test_http_route_manifest_covers_every_registered_route() -> None:
    resolved = validate_manifest(app)
    actual_operations = {
        (method, route.path)
        for route in app.routes
        if getattr(route, "methods", None)
        for method in route.methods
    }
    resolved_operations = {(method, spec.path) for spec in resolved for method in spec.methods}
    assert resolved_operations == actual_operations
    assert len(HTTP_ROUTE_MANIFEST) == len(
        {getattr(route, "name", None) for route in app.routes if getattr(route, "methods", None)}
    )


def test_non_http_registry_is_complete_and_unique() -> None:
    validate_operation_registry()
    entries = GRAPHQL_OPERATION_MANIFEST + WEBSOCKET_OPERATION_MANIFEST
    assert len({entry.operation_name for entry in entries}) == len(entries)
    assert all(entry.action and entry.resource_type and entry.endpoint for entry in entries)


def test_read_surfaces_use_their_specific_canonical_actions() -> None:
    assert HTTP_ROUTE_MANIFEST["check_connection"].action == "observability.read"
    assert HTTP_ROUTE_MANIFEST["get_observatory_preferences"].action == "settings.read"
    assert HTTP_ROUTE_MANIFEST["get_observatory_settings"].action == "settings.read"
    assert HTTP_ROUTE_MANIFEST["get_observatory_dataset_workflow_config"].action == "settings.read"
    assert HTTP_ROUTE_MANIFEST["get_observatory_search"].action == "admin.read"
    assert HTTP_ROUTE_MANIFEST["get_observatory_row_journey"].resource_keys == (
        "table_id",
        "row_id",
    )


def test_path_resource_identity_includes_every_scoped_read_key() -> None:
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/observatory/row-journey/orders/row-7",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
        },
        receive,
    )
    spec = OperationSpec(
        operation_name="row_journey",
        surface="http",
        action="dataset.read",
        resource_type="dataset",
        resource_keys=("table_id", "row_id"),
    )

    resource = asyncio.run(
        resolve_resource(request, spec, {"table_id": "orders", "row_id": "row-7"})
    )

    assert resource.resource_id == "table_id=orders|row_id=row-7"


def test_unclassified_route_fails_mechanical_validation() -> None:
    candidate = FastAPI()

    @candidate.get("/unclassified")
    def unclassified() -> dict[str, bool]:
        return {"ok": True}

    with pytest.raises(RuntimeError, match="unclassified"):
        validate_manifest(candidate)


def test_anonymous_protected_request_is_401_before_handler(monkeypatch, tmp_path) -> None:
    from phlo_api import main

    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    called = False

    def load_config() -> dict[str, str]:
        nonlocal called
        called = True
        return {"name": "should-not-run"}

    monkeypatch.setattr(main, "load_phlo_config", load_config)
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: None)

    response = TestClient(app).get("/api/config")

    assert response.status_code == 401
    assert called is False


def test_detailed_health_summary_is_protected(monkeypatch) -> None:
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: None)

    response = TestClient(app).get("/api/observability/health")

    assert response.status_code == 401


def test_unknown_path_remains_a_safe_404() -> None:
    response = TestClient(app).get("/api/does-not-exist")

    assert response.status_code == 404


def test_authenticated_principal_without_permission_is_403(monkeypatch, tmp_path) -> None:
    from phlo_api import main

    auth, canonical = _principal()
    backend = _Backend(allowed=False)
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: auth)
    monkeypatch.setattr(
        "phlo_api.security_manifest.resolve_request_principal",
        lambda _request, require_auth=True: canonical,
    )
    monkeypatch.setattr("phlo_api.security_manifest.get_authorization_backend", lambda: backend)
    monkeypatch.setattr(main, "load_phlo_config", lambda: {"name": "should-not-run"})

    response = TestClient(app).get("/api/config", headers={"Authorization": "Bearer viewer"})

    assert response.status_code == 403
    assert response.json() == {"error": "forbidden", "reason": "access_denied"}
    assert backend.calls and backend.calls[0][1] == "platform_metadata.read"


def test_scoped_principal_is_allowed_and_resource_is_checked(monkeypatch, tmp_path) -> None:
    from phlo_api import main

    auth, canonical = _principal("operator")
    backend = _Backend(allowed=True)
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    (tmp_path / "phlo.yaml").write_text("name: allowed\n")
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: auth)
    monkeypatch.setattr(
        "phlo_api.security_manifest.resolve_request_principal",
        lambda _request, require_auth=True: canonical,
    )
    monkeypatch.setattr("phlo_api.security_manifest.get_authorization_backend", lambda: backend)
    monkeypatch.setattr(main, "load_phlo_config", lambda: {"name": "allowed"})

    response = TestClient(app).get("/api/config", headers={"Authorization": "Bearer operator"})

    assert response.status_code == 200
    assert response.json() == {"name": "allowed"}
    assert backend.calls[0] == ("operator", "platform_metadata.read", "project")


def test_authorization_receives_request_correlation_before_handler(monkeypatch, tmp_path) -> None:
    auth, canonical = _principal("operator")
    backend = _Backend(allowed=True)
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    (tmp_path / "phlo.yaml").write_text("name: allowed\n")
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: auth)
    monkeypatch.setattr(
        "phlo_api.security_manifest.resolve_request_principal",
        lambda _request, require_auth=True: canonical,
    )
    monkeypatch.setattr("phlo_api.security_manifest.get_authorization_backend", lambda: backend)

    response = TestClient(app).get(
        "/api/config",
        headers={"Authorization": "Bearer operator", "X-Request-Id": "corr-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "corr-123"
    assert backend.contexts[0].request_id == "corr-123"


def test_authenticated_request_without_backend_is_503(monkeypatch) -> None:
    auth, canonical = _principal("operator")
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: auth)
    monkeypatch.setattr(
        "phlo_api.security_manifest.resolve_request_principal",
        lambda _request, require_auth=True: canonical,
    )
    monkeypatch.setattr("phlo_api.security_manifest.get_authorization_backend", lambda: None)

    response = TestClient(app).get("/api/config", headers={"Authorization": "Bearer operator"})

    assert response.status_code == 503
    assert response.json() == {
        "error": "service_unavailable",
        "reason": "authorization_unavailable",
    }


def test_composite_body_resources_are_authorized_as_one_deterministic_identity(monkeypatch) -> None:
    auth, canonical = _principal("analyst")
    backend = _Backend(allowed=False)
    monkeypatch.setattr("phlo_api.security_manifest.get_request_principal", lambda _request: auth)
    monkeypatch.setattr(
        "phlo_api.security_manifest.resolve_request_principal",
        lambda _request, require_auth=True: canonical,
    )
    monkeypatch.setattr("phlo_api.security_manifest.get_authorization_backend", lambda: backend)

    response = TestClient(app).post(
        "/api/observatory/query",
        json={"dataset_id": "orders", "table_name": "payments", "sql": "select 1"},
        headers={"Authorization": "Bearer analyst"},
    )

    assert response.status_code == 403
    assert backend.calls == [("analyst", "dataset.query", "dataset_id=orders|table_name=payments")]


def test_path_body_identity_mismatch_is_rejected_before_authorization() -> None:
    from phlo_api.security_manifest import OperationSpec, resolve_resource

    async def receive():
        return {
            "type": "http.request",
            "body": json.dumps({"dataset_id": "payments"}).encode(),
            "more_body": False,
        }

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/datasets/orders",
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", b"25"),
            ],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
        },
        receive,
    )
    spec = OperationSpec(
        operation_name="test",
        surface="http",
        action="dataset.read",
        resource_type="dataset",
        resource_keys=("dataset_id",),
    )

    with pytest.raises(Exception, match="ambiguous_resource"):
        asyncio.run(resolve_resource(request, spec, {"dataset_id": "orders"}))
