"""Tests for oauth2-proxy service plugin."""

from phlo_oauth2_proxy.plugin import Oauth2ProxyServicePlugin


def test_oauth2_proxy_service_definition():
    """Validate oauth2-proxy service metadata in compose definition."""
    plugin = Oauth2ProxyServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "oauth2-proxy"
    assert defn["category"] == "auth"
    assert defn["default"] is False
    assert defn["profile"] == "proxy"


def test_oauth2_proxy_plugin_metadata():
    """Validate oauth2-proxy plugin metadata tags and name."""
    plugin = Oauth2ProxyServicePlugin()
    meta = plugin.metadata

    assert meta.name == "oauth2-proxy"
    assert "auth" in meta.tags
    assert "oidc" in meta.tags


def test_oauth2_proxy_not_publicly_routed():
    """Verify oauth2-proxy has no traefik.enable label (internal only)."""
    plugin = Oauth2ProxyServicePlugin()
    defn = plugin.service_definition
    labels = defn.get("compose", {}).get("labels", {})

    assert labels.get("traefik.enable") != "true"


def test_oauth2_proxy_image_pinned():
    """Verify oauth2-proxy uses a pinned image version."""
    plugin = Oauth2ProxyServicePlugin()
    defn = plugin.service_definition

    assert defn["image"] == "phlo/oauth2-proxy:v7.15.3-grpc1.82.1"
    assert defn["build"]["dockerfile"] == "oauth2-proxy/Dockerfile"
