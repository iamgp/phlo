"""Tests for phlo-api authorization helpers."""

from __future__ import annotations

from fastapi import Request

from phlo.capabilities import AuthorizationPolicyBackendSpec, clear_capabilities
from phlo.capabilities.authorization import DefaultAuthorizationPolicyBackend
from phlo.capabilities.interfaces import Principal
from phlo.capabilities.registry import register_authorization_policy_backend
from phlo_api.api.authorization import (
    get_authorization_backend,
    resolve_request_principal,
)


def teardown_function() -> None:
    clear_capabilities()


def _make_request(headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": headers or [],
        }
    )


def test_resolve_request_principal_ignores_forwarded_identity_headers() -> None:
    request = _make_request(
        [
            (b"x-forwarded-user", b"admin"),
            (b"x-forwarded-roles", b"admin,operator"),
        ]
    )

    principal = resolve_request_principal(request)

    assert principal == Principal(
        subject="anonymous",
        principal_type="user",
        roles=(),
    )


def test_get_authorization_backend_requires_explicit_selection_for_multiple_backends(
    monkeypatch,
) -> None:
    register_authorization_policy_backend(
        AuthorizationPolicyBackendSpec(
            name="default",
            provider=DefaultAuthorizationPolicyBackend(
                policies=[
                    {
                        "policy_id": "allow-default",
                        "effect": "allow",
                        "action": "*",
                        "resource": {"type": "*", "id_pattern": "*"},
                    }
                ]
            ),
        )
    )
    register_authorization_policy_backend(
        AuthorizationPolicyBackendSpec(
            name="opa",
            provider=DefaultAuthorizationPolicyBackend(
                policies=[
                    {
                        "policy_id": "allow-opa",
                        "effect": "allow",
                        "action": "*",
                        "resource": {"type": "*", "id_pattern": "*"},
                    }
                ]
            ),
        )
    )

    monkeypatch.delenv("PHLO_AUTHORIZATION_BACKEND", raising=False)

    try:
        get_authorization_backend()
    except RuntimeError as exc:
        assert "Multiple authorization backends are registered" in str(exc)
    else:
        raise AssertionError("Expected explicit backend selection error")


def test_get_authorization_backend_resolves_named_backend(monkeypatch) -> None:
    backend = DefaultAuthorizationPolicyBackend(
        policies=[
            {
                "policy_id": "allow-opa",
                "effect": "allow",
                "action": "*",
                "resource": {"type": "*", "id_pattern": "*"},
            }
        ]
    )
    register_authorization_policy_backend(
        AuthorizationPolicyBackendSpec(name="default", provider=DefaultAuthorizationPolicyBackend())
    )
    register_authorization_policy_backend(
        AuthorizationPolicyBackendSpec(name="opa", provider=backend)
    )

    monkeypatch.setenv("PHLO_AUTHORIZATION_BACKEND", "opa")

    assert get_authorization_backend() is backend
