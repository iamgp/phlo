"""Authentication helpers for phlo-api.

This module provides authentication capability integration for FastAPI routes.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request

from phlo.capabilities import (
    AuthPrincipal,
    AuthResult,
    AuthenticationProvider,
    RequestContext,
    list_capabilities,
    resolve_capability,
)
from phlo.logging import get_logger

logger = get_logger(__name__)

_AUTHENTICATION_PROVIDER_ENV = "PHLO_AUTHENTICATION_PROVIDER"


def get_authentication_provider() -> AuthenticationProvider | None:
    """Resolve the authentication provider capability.

    Returns None if no provider is configured.
    Raises when multiple providers are installed without explicit selection.
    """
    provider_name = os.environ.get(_AUTHENTICATION_PROVIDER_ENV)
    result = resolve_capability("authentication_provider", provider_name)
    if provider_name and result is None:
        raise RuntimeError(
            f"Authentication provider {provider_name!r} is not registered. "
            f"Set {_AUTHENTICATION_PROVIDER_ENV} to a valid provider name."
        )

    if result is None:
        available_providers = list_capabilities("authentication_provider")
        if not available_providers:
            logger.debug("no_authentication_provider_configured")
            return None
        if provider_name is None and len(available_providers) > 1:
            raise RuntimeError(
                "Multiple authentication providers are registered. "
                f"Set {_AUTHENTICATION_PROVIDER_ENV} to one of: {', '.join(sorted(available_providers))}."
            )
        logger.debug("no_authentication_provider_configured")
        return None
    return result.provider


def require_authentication_provider() -> AuthenticationProvider:
    """Resolve the authentication provider or raise if not available."""
    provider = get_authentication_provider()
    if provider is None:
        raise RuntimeError("Authentication provider not configured")
    return provider


def create_request_context(request: Request) -> RequestContext:
    """Create a RequestContext from a FastAPI request."""
    headers_dict: dict[str, str] = {}
    for key, value in request.headers.items():
        headers_dict[key.lower()] = value
    cookies_dict = dict(request.cookies)
    query_params_dict = dict(request.query_params)

    return RequestContext(
        headers=headers_dict,
        cookies=cookies_dict,
        query_params=query_params_dict,
        method=request.method,
        path=request.url.path,
        remote_addr=request.client.host if request.client else None,
    )


_AUTH_PRINCIPAL_CACHE_KEY = "_phlo_auth_principal"
_AUTH_RESULT_CACHE_KEY = "_phlo_auth_result"


def authenticate_request(request: Request) -> AuthResult:
    """Authenticate a request using the configured authentication provider.

    Returns an AuthResult that indicates whether authentication succeeded.
    Caches the result in request.state to avoid duplicate authentication.
    """
    if hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
        return request.state[_AUTH_RESULT_CACHE_KEY]

    provider = get_authentication_provider()
    if provider is None:
        result = AuthResult(
            authenticated=False,
            reason_code="provider_unavailable",
        )
        request.state[_AUTH_RESULT_CACHE_KEY] = result
        return result

    request_context = create_request_context(request)
    result = provider.authenticate(request_context)
    request.state[_AUTH_RESULT_CACHE_KEY] = result
    return result


def get_request_principal(request: Request) -> AuthPrincipal | None:
    """Get the authenticated principal from the request.

    Returns None if no authentication provider is configured or authentication failed.
    Caches the result in request.state to avoid duplicate authentication.
    """
    if hasattr(request.state, _AUTH_PRINCIPAL_CACHE_KEY):
        return request.state[_AUTH_PRINCIPAL_CACHE_KEY]

    provider = get_authentication_provider()
    if provider is None:
        request.state[_AUTH_PRINCIPAL_CACHE_KEY] = None
        return None

    request_context = create_request_context(request)
    principal = provider.current_principal(request_context)
    request.state[_AUTH_PRINCIPAL_CACHE_KEY] = principal
    return principal


def require_principal(request: Request) -> AuthPrincipal:
    """Get the authenticated principal from the request or raise 401.

    Raises HTTPException 401 if authentication failed or no provider is configured.
    Uses cached result from request.state if available.
    """
    if hasattr(request.state, _AUTH_PRINCIPAL_CACHE_KEY):
        cached = request.state[_AUTH_PRINCIPAL_CACHE_KEY]
        if cached is not None:
            return cached
        if cached is None and not hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
            raise HTTPException(
                status_code=401,
                detail={"error": "unauthorized", "reason": "no_auth_result"},
            )

    if hasattr(request.state, _AUTH_RESULT_CACHE_KEY):
        result = request.state[_AUTH_RESULT_CACHE_KEY]
    else:
        provider = get_authentication_provider()
        if provider is None:
            logger.warning("authentication_provider_not_configured")
            raise HTTPException(
                status_code=401,
                detail={"error": "unauthorized", "reason": "provider_unavailable"},
            )
        request_context = create_request_context(request)
        result = provider.authenticate(request_context)
        request.state[_AUTH_RESULT_CACHE_KEY] = result

    if not result.authenticated:
        logger.warning(
            "authentication_failed",
            reason_code=result.reason_code,
            path=request.url.path,
            method=request.method,
        )
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": result.reason_code},
        )

    if result.principal is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "reason": "invalid_identity_payload"},
        )

    request.state[_AUTH_PRINCIPAL_CACHE_KEY] = result.principal
    return result.principal


def optional_authenticate(request: Request) -> AuthPrincipal | None:
    """Attempt to authenticate a request, returning None if not authenticated.

    Unlike require_principal, this does not raise on authentication failure.
    Useful for routes that have different behavior for authenticated vs anonymous.
    """
    provider = get_authentication_provider()
    if provider is None:
        return None

    request_context = create_request_context(request)
    result = provider.authenticate(request_context)

    if result.authenticated and result.principal is not None:
        return result.principal

    return None


def get_capabilities_metadata() -> dict[str, Any]:
    """Get metadata about available authentication capabilities."""
    available_providers = list_capabilities("authentication_provider")
    current_provider = os.environ.get(_AUTHENTICATION_PROVIDER_ENV)

    return {
        "available_providers": available_providers,
        "current_provider": current_provider,
        "environment_variable": _AUTHENTICATION_PROVIDER_ENV,
    }
