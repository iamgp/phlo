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


def _build_info(
    headers: dict[str, str],
    *,
    operation_name: str | None = "LaunchRun",
    field_name: str = "launchPipelineRun",
    parent_type_name: str = "Mutation",
    path_prev: object | None = None,
) -> SimpleNamespace:
    request = SimpleNamespace(headers=headers, remote_addr="127.0.0.1")
    context = SimpleNamespace(request=request)
    operation = SimpleNamespace(
        name=SimpleNamespace(value=operation_name) if operation_name is not None else None,
        operation=SimpleNamespace(value="mutation"),
    )
    parent_type = SimpleNamespace(name=parent_type_name)
    path = SimpleNamespace(prev=path_prev)
    return SimpleNamespace(
        context=context,
        operation=operation,
        field_name=field_name,
        parent_type=parent_type,
        path=path,
    )


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


@patch("phlo_dagster.authorization_middleware.enforce")
def test_authorize_mutation_uses_field_name_for_action_and_resource(mock_enforce, monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    token = create_service_token("phlo-api")
    info = _build_info(
        {"Authorization": f"Bearer {token}"},
        operation_name=None,
        field_name="terminateRun",
    )
    mock_enforce.return_value = MagicMock(allowed=True, reason_code=None)

    DagsterGraphQLAuthorizationMiddleware()._authorize_mutation(info, {})

    kwargs = mock_enforce.call_args.kwargs
    assert kwargs["action"] == "run.execute"
    assert kwargs["resource"].resource_type == "run"
    assert kwargs["resource"].resource_id == "dagster:terminateRun"


def test_map_operation_to_action_defaults_to_admin_manage() -> None:
    middleware = DagsterGraphQLAuthorizationMiddleware()

    assert middleware._map_operation_to_action("customMutation") == "admin.manage"
    assert middleware._map_operation_to_action(None) == "admin.manage"


def test_get_selection_resource_defaults_to_admin() -> None:
    middleware = DagsterGraphQLAuthorizationMiddleware()

    assert middleware._get_selection_resource("customMutation") == ("admin", None)
    assert middleware._get_selection_resource(None) == ("admin", None)


@patch("phlo_dagster.authorization_middleware.is_regulated", return_value=True)
@patch("phlo_dagster.authorization_middleware.enforce")
def test_resolve_skips_nested_mutation_fields(mock_enforce, _mock_regulated):
    middleware = DagsterGraphQLAuthorizationMiddleware()
    next_fn = MagicMock(return_value="ok")
    info = _build_info(
        {}, field_name="run", parent_type_name="LaunchRunSuccess", path_prev=object()
    )

    result = middleware.resolve(next_fn, None, info)

    assert result == "ok"
    mock_enforce.assert_not_called()
