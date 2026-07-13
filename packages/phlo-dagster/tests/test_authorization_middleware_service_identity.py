"""Tests for Dagster middleware service identity and correlation handling."""

from __future__ import annotations

import hashlib
import hmac
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from graphql import GraphQLError

from phlo.security.service_identity import (
    PHLO_CORRELATION_HEADER,
    PHLO_INITIATOR_HEADER,
    create_service_token,
)
from phlo_dagster.authorization_middleware import DagsterGraphQLAuthorizationMiddleware
from _oidc_test_helpers import (
    AUDIENCE,
    ISSUER,
    JWKS_URL,
    JWKSResponse,
    key_and_jwks,
    token,
)


def _build_info(
    headers: dict[str, str],
    *,
    operation_name: str | None = "LaunchRun",
    field_name: str = "launchRun",
    parent_type_name: str = "Mutation",
    path_prev: object | None = None,
    operation_kind: str = "mutation",
    remote_addr: str = "127.0.0.1",
) -> SimpleNamespace:
    request = SimpleNamespace(
        headers=headers,
        remote_addr=remote_addr,
        path="/graphql",
        method="POST",
    )
    context = SimpleNamespace(request=request)
    operation = SimpleNamespace(
        name=SimpleNamespace(value=operation_name) if operation_name is not None else None,
        operation=SimpleNamespace(value=operation_kind),
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


def test_extract_principal_rejects_unsigned_or_invalid_bearer(monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")

    for value in ("arbitrary-user-token", "phlo-api:malformed"):
        info = _build_info({"Authorization": f"Bearer {value}"})
        assert DagsterGraphQLAuthorizationMiddleware()._extract_principal(info) is None


def test_extract_principal_rejects_expired_service_token(monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    timestamp = str(int(time.time()) - 1000)
    message = f"phlo-api:{timestamp}:expired-nonce"
    signature = hmac.new(b"test-secret", message.encode(), hashlib.sha256).hexdigest()
    token = f"{message}:{signature}"

    assert (
        DagsterGraphQLAuthorizationMiddleware()._extract_principal(
            _build_info({"Authorization": f"Bearer {token}"})
        )
        is None
    )


def test_extract_principal_rejects_wrong_audience_and_unsigned_headers(monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    wrong_audience = create_service_token("untrusted-service")
    middleware = DagsterGraphQLAuthorizationMiddleware()

    assert (
        middleware._extract_principal(_build_info({"Authorization": f"Bearer {wrong_audience}"}))
        is None
    )
    assert middleware._extract_principal(_build_info({"X-Dagster-User": "forged-user"})) is None
    assert (
        middleware._extract_principal(_build_info({"X-Dagster-Api-Token": "forged-token"})) is None
    )


def test_extract_principal_accepts_only_verified_oidc_access_token(monkeypatch):
    private_key, jwks = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )

    principal = DagsterGraphQLAuthorizationMiddleware()._extract_principal(
        _build_info(
            {"X-Auth-Request-Access-Token": token(private_key, groups=["viewer", "analyst"])}
        )
    )

    assert principal is not None
    assert principal.subject == "viewer@example.com"
    assert principal.groups == ("viewer", "analyst")
    assert principal.attributes["authentication_source"] == "oidc"
    direct = DagsterGraphQLAuthorizationMiddleware()._extract_principal(
        _build_info({"Authorization": f"Bearer {token(private_key)}"})
    )
    assert direct is not None
    assert direct.subject == "viewer@example.com"


def test_extract_principal_rejects_invalid_oidc_claims_and_forged_proxy_headers(monkeypatch):
    private_key, jwks = key_and_jwks()
    another_key, _ = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )
    middleware = DagsterGraphQLAuthorizationMiddleware()

    invalid_tokens = (
        token(another_key),
        token(private_key, issuer="https://wrong.example/"),
        token(private_key, audience="wrong-audience"),
        token(private_key, expires_in=-1000),
        token(private_key, not_before=int(time.time()) + 1000),
    )
    for invalid in invalid_tokens:
        assert (
            middleware._extract_principal(_build_info({"X-Auth-Request-Access-Token": invalid}))
            is None
        )

    assert (
        middleware._extract_principal(
            _build_info(
                {
                    "X-Auth-Request-User": "forged@example.com",
                    "X-Auth-Request-Groups": "admin",
                }
            )
        )
        is None
    )


@patch("phlo_dagster.authorization_middleware.enforce")
def test_verified_oidc_viewer_reaches_http_graphql_authorization(mock_enforce, monkeypatch):
    private_key, jwks = key_and_jwks()
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_JWKS_URL", JWKS_URL)
    monkeypatch.setenv("PHLO_DAGSTER_OIDC_ALLOW_INSECURE_HTTP", "true")
    monkeypatch.setattr(
        "phlo_dagster.oidc_identity.httpx.stream",
        lambda *_args, **_kwargs: JWKSResponse(jwks),
    )
    mock_enforce.return_value = MagicMock(allowed=True, reason_code=None)
    info = _build_info(
        {"X-Auth-Request-Access-Token": token(private_key)},
        field_name="runsOrError",
        parent_type_name="Query",
        operation_kind="query",
    )

    assert (
        DagsterGraphQLAuthorizationMiddleware().resolve(lambda *_args, **_kwargs: "ok", None, info)
        == "ok"
    )
    assert mock_enforce.call_args.kwargs["action"] == "run.read"


def test_mandatory_mode_cannot_be_disabled():
    import pytest

    with pytest.raises(ValueError, match="mandatory"):
        DagsterGraphQLAuthorizationMiddleware(strict_mode=False)


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
    assert kwargs["action"] == "run.manage"
    assert kwargs["resource"].resource_type == "run"
    assert kwargs["resource"].resource_id == "dagster:terminateRun"


@patch("phlo_dagster.authorization_middleware.enforce")
def test_graphql_conflicting_same_key_values_fail_closed(mock_enforce, monkeypatch):
    monkeypatch.setenv("PHLO_SERVICE_SECRET", "test-secret")
    service_token = create_service_token("phlo-api")
    info = _build_info(
        {"Authorization": f"Bearer {service_token}"},
        field_name="launchRun",
        operation_kind="mutation",
    )

    with pytest.raises(GraphQLError, match="Ambiguous GraphQL resource identity"):
        DagsterGraphQLAuthorizationMiddleware()._authorize_field(
            info,
            {"selector": {"runId": "run-a"}, "reexecution": {"runId": "run-b"}},
        )

    mock_enforce.assert_not_called()


def test_map_operation_to_action_rejects_unclassified_fields() -> None:
    middleware = DagsterGraphQLAuthorizationMiddleware()

    import pytest

    with pytest.raises(RuntimeError, match="Unclassified"):
        middleware._map_operation_to_action("customMutation")
    with pytest.raises(Exception, match="Unclassified"):
        middleware._map_operation_to_action(None)


def test_get_selection_resource_rejects_unclassified_fields() -> None:
    middleware = DagsterGraphQLAuthorizationMiddleware()

    import pytest

    with pytest.raises(RuntimeError, match="Unclassified"):
        middleware._get_selection_resource("customMutation")
    with pytest.raises(Exception, match="Unclassified"):
        middleware._get_selection_resource(None)


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
