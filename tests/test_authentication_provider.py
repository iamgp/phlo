"""Tests for authentication provider capability."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from phlo.capabilities import (
    RequestContext,
    clear_capabilities,
)
from phlo.capabilities.authentication import (
    ProxyAuthenticationProvider,
    ServiceTokenAuthenticationProvider,
    StaticAuthenticationProvider,
    register_default_capability_providers,
)
from phlo.capabilities.registry import get_capability_registry


@pytest.fixture(autouse=True)
def clear_auth_providers():
    """Clear auth providers before and after each test."""
    clear_capabilities()
    yield
    clear_capabilities()


class TestStaticAuthenticationProvider:
    """Tests for StaticAuthenticationProvider."""

    def test_authenticate_with_dev_mode(self):
        """Test authentication succeeds in dev mode."""
        provider = StaticAuthenticationProvider(dev_mode=True)
        request_context = RequestContext(
            headers={},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.subject == "dev_user"
        assert result.principal.principal_type == "user"

    def test_authenticate_without_credentials_fails(self):
        """Test authentication fails without credentials when not in dev mode."""
        provider = StaticAuthenticationProvider(dev_mode=False)
        request_context = RequestContext(
            headers={},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "missing_credentials"

    def test_authenticate_with_valid_token(self):
        """Test authentication succeeds with valid static token."""
        provider = StaticAuthenticationProvider(
            static_users={"test-token": {"subject": "test-user", "email": "test@example.com"}}
        )
        request_context = RequestContext(
            headers={"authorization": "Bearer test-token"},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.subject == "test-user"
        assert result.principal.email == "test@example.com"

    def test_authenticate_with_invalid_token_fails(self):
        """Test authentication fails with invalid token."""
        provider = StaticAuthenticationProvider(static_users={})
        request_context = RequestContext(
            headers={"authorization": "Bearer invalid-token"},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "missing_credentials"


class TestServiceTokenAuthenticationProvider:
    """Tests for ServiceTokenAuthenticationProvider."""

    def test_authenticate_with_valid_service_token(self):
        """Test authentication succeeds with valid service token."""
        provider = ServiceTokenAuthenticationProvider(
            service_tokens={
                "service-token-123": {
                    "subject": "my-service",
                    "principal_type": "service",
                }
            }
        )
        request_context = RequestContext(
            headers={"authorization": "Bearer service-token-123"},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.subject == "my-service"
        assert result.principal.principal_type == "service"

    def test_authenticate_with_invalid_service_token_fails(self):
        """Test authentication fails with invalid service token."""
        provider = ServiceTokenAuthenticationProvider(service_tokens={})
        request_context = RequestContext(
            headers={"authorization": "Bearer invalid"},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "missing_credentials"

    def test_authenticate_without_token_fails(self):
        """Test authentication fails without any token."""
        provider = ServiceTokenAuthenticationProvider(service_tokens={})
        request_context = RequestContext(
            headers={},
            cookies={},
            query_params={},
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "missing_credentials"


class TestProxyAuthenticationProvider:
    """Tests for ProxyAuthenticationProvider."""

    def test_authenticate_from_trusted_proxy(self):
        """Test authentication succeeds from trusted proxy IP."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["127.0.0.1/32", "192.168.1.0/24"])
        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
                "x-remote-email": "proxy@example.com",
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.subject == "proxy-user"
        assert result.principal.email == "proxy@example.com"

    def test_authenticate_from_untrusted_ip_fails(self):
        """Test authentication fails from untrusted IP."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["10.0.0.1/32"])
        request_context = RequestContext(
            headers={"x-remote-user": "proxy-user"},
            cookies={},
            query_params={},
            remote_addr="192.168.1.100",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"

    def test_authenticate_without_remote_addr_fails(self):
        """Test authentication fails when remote address is unknown."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["127.0.0.1/32"])
        request_context = RequestContext(
            headers={"x-remote-user": "proxy-user"},
            cookies={},
            query_params={},
            remote_addr=None,
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"

    def test_authenticate_without_header_fails(self):
        """Test authentication fails when proxy header is missing."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["127.0.0.1/32"])
        request_context = RequestContext(
            headers={},
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "missing_credentials"

    def test_cidr_network_matching(self):
        """Test CIDR network matching works correctly."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["192.168.0.0/16"])

        assert provider._is_from_trusted_proxy(
            RequestContext(headers={}, cookies={}, query_params={}, remote_addr="192.168.1.100")
        )
        assert provider._is_from_trusted_proxy(
            RequestContext(headers={}, cookies={}, query_params={}, remote_addr="192.168.255.255")
        )
        assert not provider._is_from_trusted_proxy(
            RequestContext(headers={}, cookies={}, query_params={}, remote_addr="10.0.0.1")
        )
        assert not provider._is_from_trusted_proxy(
            RequestContext(headers={}, cookies={}, query_params={}, remote_addr="172.16.0.1")
        )


class TestAuthenticationProviderRegistration:
    """Tests for authentication provider registration."""

    def test_register_default_providers_explicit_env(self):
        """Test providers are registered when explicitly enabled via env."""
        with patch.dict(os.environ, {"PHLO_AUTH_STATIC_ENABLED": "true"}):
            clear_capabilities()
            register_default_capability_providers()
            registry = get_capability_registry()
            providers = registry.list_authentication_providers()
            assert len(providers) == 1
            assert providers[0].name == "static"

    def test_no_auto_registration_by_default(self):
        """Test providers are NOT auto-registered without explicit env."""
        env_to_clear = [
            "PHLO_AUTH_STATIC_ENABLED",
            "PHLO_AUTH_PROXY_ENABLED",
            "PHLO_AUTH_SERVICE_ENABLED",
            "PHLO_AUTH_DEV_MODE",
        ]
        with patch.dict(os.environ, dict.fromkeys(env_to_clear, ""), clear=True):
            clear_capabilities()
            register_default_capability_providers()
            registry = get_capability_registry()
            providers = registry.list_authentication_providers()
            assert len(providers) == 0


class TestProviderSelection:
    """Tests for provider selection logic."""

    def test_multiple_providers_require_explicit_selection(self):
        """Test that multiple providers require explicit selection."""
        with patch.dict(
            os.environ,
            {
                "PHLO_AUTH_STATIC_ENABLED": "true",
                "PHLO_AUTH_PROXY_ENABLED": "true",
            },
        ):
            clear_capabilities()
            register_default_capability_providers()
            registry = get_capability_registry()
            providers = registry.list_authentication_providers()
            assert len(providers) == 2
            names = {p.name for p in providers}
            assert "static" in names
            assert "proxy" in names
