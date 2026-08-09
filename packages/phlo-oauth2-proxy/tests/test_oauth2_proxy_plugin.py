"""Tests for oauth2-proxy service plugin."""

from importlib.resources import files

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

    assert defn["image"] == "ghcr.io/phlohouse/phlo-oauth2-proxy:v7.15.3-grpc1.82.1"
    assert defn["build"]["dockerfile"] == "oauth2-proxy/Dockerfile"


def test_oauth2_proxy_image_pins_the_fixed_xtext_dependency() -> None:
    """The generated image must contain the scanner-required x/text fix."""
    dockerfile = files("phlo_oauth2_proxy").joinpath("Dockerfile").read_text()

    assert "golang.org/x/text@v0.39.0" in dockerfile


def test_oauth2_proxy_uses_a_distroless_readiness_probe():
    """The generated image must not depend on absent shell utilities."""
    definition = Oauth2ProxyServicePlugin().service_definition

    assert definition["compose"]["healthcheck"]["test"] == [
        "CMD",
        "/bin/oauth2-proxy-healthcheck",
    ]
    assert any(
        file["dest"] == "oauth2-proxy/oauth2_proxy_healthcheck.go" for file in definition["files"]
    )
