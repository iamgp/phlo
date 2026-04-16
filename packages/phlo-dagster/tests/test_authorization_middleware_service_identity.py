"""Tests for Dagster middleware service identity and correlation handling."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from phlo.security.service_identity import (
    PHLO_CORRELATION_HEADER,
    PHLO_INITIATOR_HEADER,
    create_service_token,
)
from phlo_dagster.authorization_middleware import DagsterGraphQLAuthorizationMiddleware


def _build_info(headers: dict[str, str]) -> SimpleNamespace:
    request = SimpleNamespace(headers=headers, remote_addr="127.0.0.1")
    context = SimpleNamespace(request=request)
    operation = SimpleNamespace(
        name=SimpleNamespace(value="LaunchRun"),
        operation=SimpleNamespace(value="mutation"),
    )
    return SimpleNamespace(context=context, operation=operation)


def test_extract_principal_from_service_token(monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    token = create_service_token("phlo-api")
    info = _build_info(
        {
            "Authorization": f"Bearer {token}",
            PHLO_INITIATOR_HEADER: "alice@example.com",
        }
    )

    principal = DagsterGraphQLAuthorizationMiddleware()._extract_principal(info)

    assert principal is not None
    assert principal.subject == "service:phlo-api"
    assert principal.principal_type == "service"
    assert principal.attributes["authentication_source"] == "service_token"
    assert principal.attributes["initiating_principal"] == "alice@example.com"


def test_create_decision_context_prefers_correlation_header():
    info = _build_info({PHLO_CORRELATION_HEADER: "corr-123"})

    context = DagsterGraphQLAuthorizationMiddleware()._create_decision_context(info)

    assert context.request_id == "corr-123"


@patch("phlo_dagster.authorization_middleware.enforce")
def test_authorize_mutation_passes_correlation_id(mock_enforce, monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    token = create_service_token("phlo-api")
    info = _build_info(
        {
            "Authorization": f"Bearer {token}",
            PHLO_CORRELATION_HEADER: "corr-456",
        }
    )
    mock_enforce.return_value = MagicMock(allowed=True, reason_code=None)

    DagsterGraphQLAuthorizationMiddleware()._authorize_mutation(info, {})

    kwargs = mock_enforce.call_args.kwargs
    assert kwargs["request_id"] == "corr-456"
    assert kwargs["correlation_id"] == "corr-456"
