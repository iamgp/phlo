"""Tests for Loki service plugin."""

from phlo_loki.plugin import LokiServicePlugin


def test_loki_service_definition():
    """Validate Loki service definition fields."""

    plugin = LokiServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "loki"
    assert defn["profile"] == "observability"
    assert "loki-data:/loki" in defn["compose"]["volumes"]
    assert "./volumes/loki:/loki" not in defn["compose"]["volumes"]


def test_loki_service_builds_patched_release_image() -> None:
    """Generated Loki uses the stable release with its fixed gRPC dependency."""
    definition = LokiServicePlugin().service_definition

    assert definition["image"] == "ghcr.io/phlohouse/phlo-loki:3.7.4-grpc1.82.1"
    assert definition["build"] == {"context": ".", "dockerfile": "loki/Dockerfile"}
    assert "LOKI_VERSION" not in definition["env_vars"]


def test_loki_uses_a_distroless_readiness_probe() -> None:
    """The generated image must not depend on absent shell utilities."""
    definition = LokiServicePlugin().service_definition

    assert definition["compose"]["healthcheck"]["test"] == [
        "CMD",
        "/usr/bin/loki-healthcheck",
    ]
    assert any(file["dest"] == "loki/loki_healthcheck.go" for file in definition["files"])


def test_loki_plugin_metadata():
    """Validate Loki plugin metadata tags and name."""

    plugin = LokiServicePlugin()
    meta = plugin.metadata

    assert meta.name == "loki"
    assert "observability" in meta.tags
