"""Tests for authentication provider capability."""

from __future__ import annotations

import hmac
import os
import time
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

    @staticmethod
    def _proxy_signature(
        secret: str,
        timestamp: str,
        remote_addr: str,
        path: str,
        subject: str = "",
        email: str = "",
        groups: str = "",
    ) -> str:
        payload = ":".join([timestamp, remote_addr, path, subject, email, groups])
        return hmac.new(secret.encode(), payload.encode(), "sha256").hexdigest()

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

    def test_authenticate_with_shared_secret_succeeds(self):
        """Test authentication succeeds with valid signature (issue #338)."""
        secret = "test-secret-123"
        provider = ProxyAuthenticationProvider(
            trusted_proxies=["127.0.0.1/32"], shared_secret=secret
        )

        timestamp = str(int(time.time()))
        signature = self._proxy_signature(
            secret,
            timestamp,
            "127.0.0.1",
            "/test/path",
            subject="proxy-user",
            email="proxy@example.com",
        )

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
                "x-remote-email": "proxy@example.com",
                "x-phlo-proxy-signature": signature,
                "x-phlo-proxy-timestamp": timestamp,
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.subject == "proxy-user"

    def test_authenticate_without_signature_fails_when_secret_configured(self):
        """Test authentication fails without signature when shared_secret is set (issue #338)."""
        provider = ProxyAuthenticationProvider(
            trusted_proxies=["127.0.0.1/32"], shared_secret="test-secret"
        )

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"

    def test_authenticate_with_invalid_signature_fails(self):
        """Test authentication fails with invalid signature (issue #338)."""
        provider = ProxyAuthenticationProvider(
            trusted_proxies=["127.0.0.1/32"], shared_secret="test-secret"
        )

        timestamp = str(int(time.time()))

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
                "x-phlo-proxy-signature": "invalid-signature",
                "x-phlo-proxy-timestamp": timestamp,
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"

    def test_authenticate_with_expired_timestamp_fails(self):
        """Test authentication fails with expired timestamp (issue #338)."""
        secret = "test-secret-123"
        provider = ProxyAuthenticationProvider(
            trusted_proxies=["127.0.0.1/32"], shared_secret=secret
        )

        timestamp = str(int(time.time()) - 600)
        signature = self._proxy_signature(secret, timestamp, "127.0.0.1", "/test/path")

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
                "x-phlo-proxy-signature": signature,
                "x-phlo-proxy-timestamp": timestamp,
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"

    def test_authenticate_without_secret_allows_unsigned_requests(self):
        """Test authentication allows unsigned requests when no shared_secret configured."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["127.0.0.1/32"])

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
                "x-remote-email": "proxy@example.com",
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.email == "proxy@example.com"

    def test_authenticate_without_email_header_keeps_email_none(self):
        """Test absent proxy email header stays None on the principal."""
        provider = ProxyAuthenticationProvider(trusted_proxies=["127.0.0.1/32"])

        request_context = RequestContext(
            headers={
                "x-remote-user": "proxy-user",
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is True
        assert result.principal is not None
        assert result.principal.email is None

    def test_authenticate_rejects_signed_request_when_identity_headers_change(self):
        """Test signature binds asserted identity fields to the authenticated principal."""
        secret = "test-secret-123"
        provider = ProxyAuthenticationProvider(
            trusted_proxies=["127.0.0.1/32"], shared_secret=secret
        )

        timestamp = str(int(time.time()))
        signature = self._proxy_signature(
            secret,
            timestamp,
            "127.0.0.1",
            "/test/path",
            subject="proxy-user",
            email="proxy@example.com",
            groups="admins,operators",
        )

        request_context = RequestContext(
            headers={
                "x-remote-user": "other-user",
                "x-remote-email": "proxy@example.com",
                "x-remote-groups": "admins,operators",
                "x-phlo-proxy-signature": signature,
                "x-phlo-proxy-timestamp": timestamp,
            },
            cookies={},
            query_params={},
            remote_addr="127.0.0.1",
            path="/test/path",
        )
        result = provider.authenticate(request_context)

        assert result.authenticated is False
        assert result.reason_code == "invalid_identity_payload"


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

    def test_register_proxy_provider_loads_shared_secret_from_environment(self):
        """Test proxy shared secret is wired through environment config."""
        with patch.dict(
            os.environ,
            {
                "PHLO_AUTH_PROXY_ENABLED": "true",
                "PHLO_AUTH_PROXY_SHARED_SECRET": "env-secret",
                "PHLO_AUTH_PROXY_TRUSTED_PROXIES": "127.0.0.1/32",
                "PHLO_AUTH_PROXY_HEADER_EMAIL": "X-Test-Email",
                "PHLO_AUTH_PROXY_HEADER_GROUPS": "X-Test-Groups",
            },
            clear=True,
        ):
            clear_capabilities()
            register_default_capability_providers()
            registry = get_capability_registry()
            providers = registry.list_authentication_providers()

            assert len(providers) == 1
            assert providers[0].name == "proxy"
            provider = providers[0].provider
            assert isinstance(provider, ProxyAuthenticationProvider)
            assert provider._shared_secret == "env-secret"
            assert provider._header_email == "x-test-email"
            assert provider._header_groups == "x-test-groups"


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
