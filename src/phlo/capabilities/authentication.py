"""Default authentication provider capability providers."""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
import secrets
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from phlo.capabilities.interfaces import (
    AuthenticatedSession,
    AuthPrincipal,
    AuthResult,
    BrowserLoginStart,
    LogoutResult,
    RequestContext,
)
from phlo.capabilities.registry import register_authentication_provider
from phlo.capabilities.specs import AuthenticationProviderSpec
from phlo.capabilities.support import CapabilitySupport
from phlo.logging import get_logger

logger = get_logger(__name__)


def _log_auth_event(
    event_type: str,
    principal: AuthPrincipal | None,
    reason_code: str,
    provider_name: str,
    auth_method: str | None = None,
    **extra: Any,
) -> None:
    """Log authentication event for audit purposes."""
    log_args = {
        "event_type": event_type,
        "reason_code": reason_code,
        "provider": provider_name,
    }
    if principal:
        log_args["subject"] = principal.subject
        log_args["principal_type"] = principal.principal_type
        if principal.issuer:
            log_args["issuer"] = principal.issuer
        if principal.email:
            log_args["email"] = principal.email
    if auth_method:
        log_args["auth_method"] = auth_method
    log_args.update(extra)

    event_name = f"authentication_{event_type}"
    log_fn = logger.info if event_type == "success" else logger.warning
    log_fn(event_name, **log_args)


class StaticAuthenticationProvider:
    """Static/local development authentication provider.

    This provider is intended for development and testing only.
    It validates against configured static users or always succeeds
    when explicitly enabled in development mode.
    """

    def __init__(
        self,
        static_users: dict[str, dict[str, Any]] | None = None,
        dev_mode: bool = False,
    ):
        self._static_users = static_users or {}
        self._dev_mode = dev_mode
        self._sessions: dict[str, AuthenticatedSession] = {}

    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using static credentials or dev mode."""
        auth_header = request_context.headers.get("authorization", "")
        cookie_session = request_context.cookies.get("phlo_session")

        if cookie_session and cookie_session in self._sessions:
            session = self._sessions[cookie_session]
            if self._is_session_valid(session):
                _log_auth_event(
                    "success",
                    session.principal,
                    "authenticated",
                    "static",
                    auth_method="session",
                    path=request_context.path,
                )
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )
            del self._sessions[cookie_session]

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = self.validate_token(token)
            if session:
                _log_auth_event(
                    "success",
                    session.principal,
                    "authenticated",
                    "static",
                    auth_method="bearer_token",
                    path=request_context.path,
                )
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )
            _log_auth_event(
                "failure",
                None,
                "invalid_token",
                "static",
                auth_method="bearer_token",
                path=request_context.path,
            )

        if self._dev_mode:
            dev_principal = AuthPrincipal(
                subject="dev_user",
                principal_type="user",
                email="dev@localhost",
                groups=("admin",),
                attributes={"mode": "development"},
            )
            session = AuthenticatedSession(
                principal=dev_principal,
                auth_method="static",
                provider_name="static",
                session_id=secrets.token_urlsafe(32),
                attributes={"mode": "development"},
            )
            _log_auth_event(
                "success",
                dev_principal,
                "authenticated",
                "static",
                auth_method="static",
                path=request_context.path,
            )
            return AuthResult(
                authenticated=True,
                principal=dev_principal,
                session=session,
                reason_code="authenticated",
            )

        return AuthResult(
            authenticated=False,
            reason_code="missing_credentials",
        )

    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get current principal from request context."""
        result = self.authenticate(request_context)
        return result.principal

    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a bearer token."""
        matched_key: str | None = None
        for key in self._static_users:
            if hmac.compare_digest(key, token):
                matched_key = key
        if matched_key is not None:
            user_data = self._static_users[matched_key]
            principal = AuthPrincipal(
                subject=user_data.get("subject", token),
                principal_type=user_data.get("principal_type", "user"),
                email=user_data.get("email"),
                groups=tuple(user_data.get("groups", [])),
                claims=user_data.get("claims", {}),
                attributes=user_data.get("attributes", {}),
            )
            return AuthenticatedSession(
                principal=principal,
                auth_method="bearer_token",
                provider_name="static",
                session_id=secrets.token_urlsafe(32),
            )
        return None

    def start_login(self) -> BrowserLoginStart:
        """Start login flow (not supported in static provider)."""
        raise NotImplementedError("Static provider does not support browser login")

    def finish_login(self, request_context: RequestContext) -> AuthResult:
        """Finish login flow (not supported in static provider)."""
        raise NotImplementedError("Static provider does not support browser login")

    def logout(self, request_context: RequestContext) -> LogoutResult:
        """Log out the current user."""
        cookie_session = request_context.cookies.get("phlo_session")
        if cookie_session and cookie_session in self._sessions:
            del self._sessions[cookie_session]
        return LogoutResult(success=True)

    def _is_session_valid(self, session: AuthenticatedSession) -> bool:
        """Check if session is still valid."""
        if session.expires_at is None:
            return True
        return datetime.now(UTC) < session.expires_at


class ProxyAuthenticationProvider:
    """Reverse-proxy asserted identity authentication provider.

    This provider validates requests from trusted reverse proxies that
    assert user identity through headers. It uses CIDR notation for
    trusted proxy configuration.
    """

    def __init__(
        self,
        trusted_proxies: list[str] | None = None,
        header_subject: str = "X-Remote-User",
        header_email: str = "X-Remote-Email",
        header_groups: str = "X-Remote-Groups",
        shared_secret: str | None = None,
    ):
        self._trusted_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        self._trusted_hosts: set[str] = set()
        for proxy in trusted_proxies or ["127.0.0.1/32", "::1/128"]:
            try:
                if "/" in proxy:
                    network = ipaddress.ip_network(proxy, strict=False)
                    self._trusted_networks.append(network)
                else:
                    self._trusted_hosts.add(proxy)
            except ValueError:
                logger.warning("invalid_trusted_proxy_config", proxy=proxy)
        self._header_subject = header_subject.lower()
        self._header_email = header_email.lower()
        self._header_groups = header_groups.lower()
        self._signature_header = "x-phlo-proxy-signature"
        self._timestamp_header = "x-phlo-proxy-timestamp"
        self._shared_secret = shared_secret

    def _identity_payload_parts(self, request_context: RequestContext) -> tuple[str, str, str]:
        """Return the asserted identity fields bound into the proxy signature."""
        subject = request_context.headers.get(self._header_subject, "")
        email = request_context.headers.get(self._header_email, "")
        groups_raw = request_context.headers.get(self._header_groups, "")
        groups = ",".join(g.strip() for g in groups_raw.split(",") if g.strip())
        return subject, email, groups

    def _is_from_trusted_proxy(self, request_context: RequestContext) -> bool:
        """Check if request came from a trusted proxy using CIDR matching."""
        remote_addr = request_context.remote_addr
        if remote_addr is None:
            return False
        if remote_addr in self._trusted_hosts:
            return True
        try:
            addr = ipaddress.ip_address(remote_addr)
            for network in self._trusted_networks:
                if addr in network:
                    return True
        except ValueError:
            pass
        return False

    def _verify_proxy_signature(self, request_context: RequestContext) -> bool:
        """Verify that the request was signed by a trusted proxy with the shared secret."""
        if self._shared_secret is None:
            return True
        signature = request_context.headers.get(self._signature_header)
        timestamp_str = request_context.headers.get(self._timestamp_header)
        if not signature or not timestamp_str:
            logger.debug("missing_proxy_signature", remote_addr=request_context.remote_addr)
            return False
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            logger.debug("invalid_proxy_timestamp", timestamp=timestamp_str)
            return False
        now = datetime.now(UTC).timestamp()
        if abs(now - timestamp) > 300:
            logger.debug("expired_proxy_timestamp", timestamp=timestamp_str)
            return False
        subject, email, groups = self._identity_payload_parts(request_context)
        remote_addr = request_context.remote_addr or ""
        path = request_context.path or ""
        payload_parts: tuple[str, str, str, str, str, str] = (
            str(timestamp),
            remote_addr,
            path,
            subject,
            email,
            groups,
        )
        payload = ":".join(payload_parts)
        expected = hmac.new(self._shared_secret.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.debug("invalid_proxy_signature", remote_addr=request_context.remote_addr)
            return False
        return True

    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using proxy-asserted identity."""
        if not self._is_from_trusted_proxy(request_context):
            _log_auth_event(
                "failure",
                None,
                "invalid_identity_payload",
                "proxy",
                auth_method="proxy",
                path=request_context.path,
                remote_addr=request_context.remote_addr,
                reason="untrusted_proxy",
            )
            return AuthResult(
                authenticated=False,
                reason_code="invalid_identity_payload",
            )

        if not self._verify_proxy_signature(request_context):
            _log_auth_event(
                "failure",
                None,
                "invalid_identity_payload",
                "proxy",
                auth_method="proxy",
                path=request_context.path,
                remote_addr=request_context.remote_addr,
                reason="invalid_signature",
            )
            return AuthResult(
                authenticated=False,
                reason_code="invalid_identity_payload",
            )

        subject, email, groups_raw = self._identity_payload_parts(request_context)
        if not subject:
            _log_auth_event(
                "failure",
                None,
                "missing_credentials",
                "proxy",
                auth_method="proxy",
                path=request_context.path,
                remote_addr=request_context.remote_addr,
            )
            return AuthResult(
                authenticated=False,
                reason_code="missing_credentials",
            )

        groups = tuple(g for g in groups_raw.split(",") if g)

        principal = AuthPrincipal(
            subject=subject,
            principal_type="user",
            email=email,
            groups=groups,
            attributes={"source": "proxy"},
        )

        session = AuthenticatedSession(
            principal=principal,
            auth_method="proxy",
            provider_name="proxy",
            attributes={"remote_addr": request_context.remote_addr or "unknown"},
        )

        _log_auth_event(
            "success",
            principal,
            "authenticated",
            "proxy",
            auth_method="proxy",
            path=request_context.path,
            remote_addr=request_context.remote_addr,
        )

        return AuthResult(
            authenticated=True,
            principal=principal,
            session=session,
            reason_code="authenticated",
        )

    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get current principal from proxy headers."""
        result = self.authenticate(request_context)
        return result.principal

    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a bearer token (not supported in proxy provider)."""
        return None

    def authenticate_proxy_identity(self, request_context: RequestContext) -> AuthResult:
        """Authenticate proxy-asserted identity (explicit flow)."""
        return self.authenticate(request_context)


class ServiceTokenAuthenticationProvider:
    """Service principal/token authentication provider.

    This provider validates service accounts used for automation
    and service-to-service authentication.
    """

    def __init__(
        self,
        service_tokens: dict[str, dict[str, Any]] | None = None,
    ):
        self._service_tokens = service_tokens or {}

    def authenticate(self, request_context: RequestContext) -> AuthResult:
        """Authenticate using service token."""
        auth_header = request_context.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            session = self.validate_token(token)
            if session:
                return AuthResult(
                    authenticated=True,
                    principal=session.principal,
                    session=session,
                    reason_code="authenticated",
                )

        return AuthResult(
            authenticated=False,
            reason_code="missing_credentials",
        )

    def current_principal(self, request_context: RequestContext) -> AuthPrincipal | None:
        """Get current principal from request context."""
        result = self.authenticate(request_context)
        return result.principal

    def validate_token(self, token: str) -> AuthenticatedSession | None:
        """Validate a service token."""
        matched_key: str | None = None
        for key in self._service_tokens:
            if hmac.compare_digest(key, token):
                matched_key = key
        if matched_key is not None:
            service_data = self._service_tokens[matched_key]
            principal = AuthPrincipal(
                subject=service_data.get("subject", token),
                principal_type="service",
                issuer=service_data.get("issuer"),
                email=service_data.get("email"),
                groups=tuple(service_data.get("groups", [])),
                claims=service_data.get("claims", {}),
                attributes=service_data.get("attributes", {}),
            )
            return AuthenticatedSession(
                principal=principal,
                auth_method="bearer_token",
                provider_name="service_token",
                session_id=secrets.token_urlsafe(32),
                attributes={"service": "true"},
            )
        return None


def _load_static_config() -> tuple[dict[str, dict[str, Any]], bool]:
    """Load static authentication configuration from environment."""
    static_users = {}
    dev_mode = os.environ.get("PHLO_AUTH_DEV_MODE", "").lower() in ("1", "true", "yes")

    if dev_mode:
        environment = os.environ.get("PHLO_ENVIRONMENT", "dev").lower()
        if environment in ("production", "prod"):
            logger.error(
                "auth_dev_mode_blocked",
                reason="PHLO_AUTH_DEV_MODE is enabled but PHLO_ENVIRONMENT is production",
            )
            dev_mode = False
        else:
            logger.warning(
                "auth_dev_mode_active",
                reason="All requests authenticate as dev_user with admin privileges",
            )

    users_json = os.environ.get("PHLO_AUTH_STATIC_USERS")
    if users_json:
        with suppress(json.JSONDecodeError):
            static_users = json.loads(users_json)

    return static_users, dev_mode


def _load_proxy_config() -> dict[str, Any]:
    """Load proxy authentication configuration from environment."""
    config = {}

    trusted = os.environ.get("PHLO_AUTH_PROXY_TRUSTED_PROXIES")
    if trusted:
        config["trusted_proxies"] = [p.strip() for p in trusted.split(",")]

    header_subject = os.environ.get("PHLO_AUTH_PROXY_HEADER_SUBJECT")
    if header_subject:
        config["header_subject"] = header_subject

    header_email = os.environ.get("PHLO_AUTH_PROXY_HEADER_EMAIL")
    if header_email:
        config["header_email"] = header_email

    header_groups = os.environ.get("PHLO_AUTH_PROXY_HEADER_GROUPS")
    if header_groups:
        config["header_groups"] = header_groups

    shared_secret = os.environ.get("PHLO_AUTH_PROXY_SHARED_SECRET")
    if shared_secret:
        config["shared_secret"] = shared_secret

    return config


def _load_service_token_config() -> dict[str, dict[str, Any]]:
    """Load service token configuration from environment."""
    service_tokens = {}

    tokens_json = os.environ.get("PHLO_AUTH_SERVICE_TOKENS")
    if tokens_json:
        with suppress(json.JSONDecodeError):
            service_tokens = json.loads(tokens_json)

    return service_tokens


def register_default_capability_providers() -> None:
    """Register authentication providers only when explicitly enabled via config.

    Authentication providers are security-sensitive and must be explicitly
    enabled via environment variables, not auto-registered on startup.
    """
    static_users, dev_mode = _load_static_config()
    if static_users or dev_mode or os.environ.get("PHLO_AUTH_STATIC_ENABLED"):
        register_authentication_provider(
            AuthenticationProviderSpec(
                name="static",
                provider=StaticAuthenticationProvider(
                    static_users=static_users,
                    dev_mode=dev_mode,
                ),
                metadata={
                    "auth_method": "static",
                    "supports_browser_login": False,
                    "supports_proxy_auth": False,
                    "supports_service_tokens": True,
                    "dev_mode": dev_mode,
                },
                support=CapabilitySupport(
                    supports_permissions=False,
                    supports_attributes=True,
                ),
            )
        )

    proxy_config = _load_proxy_config()
    if proxy_config or os.environ.get("PHLO_AUTH_PROXY_ENABLED"):
        register_authentication_provider(
            AuthenticationProviderSpec(
                name="proxy",
                provider=ProxyAuthenticationProvider(**proxy_config),
                metadata={
                    "auth_method": "proxy",
                    "supports_browser_login": False,
                    "supports_proxy_auth": True,
                    "supports_service_tokens": False,
                },
                support=CapabilitySupport(
                    supports_permissions=False,
                    supports_attributes=True,
                ),
            )
        )

    service_tokens = _load_service_token_config()
    if service_tokens or os.environ.get("PHLO_AUTH_SERVICE_ENABLED"):
        register_authentication_provider(
            AuthenticationProviderSpec(
                name="service_token",
                provider=ServiceTokenAuthenticationProvider(
                    service_tokens=service_tokens,
                ),
                metadata={
                    "auth_method": "bearer_token",
                    "supports_browser_login": False,
                    "supports_proxy_auth": False,
                    "supports_service_tokens": True,
                },
                support=CapabilitySupport(
                    supports_permissions=False,
                    supports_attributes=True,
                ),
            )
        )
