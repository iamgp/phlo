"""Oauth2 Proxy service plugin registration."""

from __future__ import annotations

from phlo.plugins import service_plugin_class


Oauth2ProxyServicePlugin = service_plugin_class(
    "Oauth2ProxyServicePlugin",
    name="oauth2-proxy",
    version="0.1.0",
    description="OAuth2/OIDC authentication proxy for Phlo services",
    author="Phlo Team",
    tags=["auth", "proxy", "oidc"],
)
