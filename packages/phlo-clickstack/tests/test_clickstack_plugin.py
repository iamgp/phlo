"""Tests for ClickStack service plugin."""

from importlib import resources

from click.testing import CliRunner

from phlo_clickstack.cli import clickstack_group
from phlo_clickstack.plugin import ClickStackServicePlugin


def test_clickstack_service_definition() -> None:
    """Validate ClickStack service definition defaults."""
    plugin = ClickStackServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "clickstack"
    assert defn["profile"] == "observability"
    assert "${CLICKSTACK_PORT:-18080}:8080" in defn["compose"]["ports"]
    assert "${CLICKSTACK_HTTP_PORT:-18123}:8123" in defn["compose"]["ports"]
    assert "${CLICKSTACK_NATIVE_PORT:-19002}:9000" in defn["compose"]["ports"]
    assert not any("4317" in port or "4318" in port for port in defn["compose"]["ports"])
    assert "clickstack-data:/var/lib/clickhouse" in defn["compose"]["volumes"]
    assert "./volumes/clickstack:/var/lib/clickhouse" not in defn["compose"]["volumes"]


def test_clickstack_builds_the_patched_stable_image() -> None:
    """The generated service builds the audited stable derivative."""
    definition = ClickStackServicePlugin().service_definition
    dockerfile = resources.files("phlo_clickstack").joinpath("Dockerfile").read_text()

    assert definition["image"] == "ghcr.io/phlohouse/phlo-clickstack:2.31.0-security-patches"
    assert definition["build"] == {"context": ".", "dockerfile": "clickstack/Dockerfile"}
    assert "FROM docker.io/hyperdx/hyperdx-all-in-one:2.31.0@sha256:b01cc48" in dockerfile
    assert "docker.hyperdx.io" not in dockerfile
    assert "CLICKSTACK_IMAGE" not in definition["env_vars"]


def test_clickstack_plugin_metadata() -> None:
    """Validate ClickStack plugin metadata."""
    plugin = ClickStackServicePlugin()
    meta = plugin.metadata

    assert meta.name == "clickstack"
    assert "observability" in meta.tags


def test_clickstack_query_rejects_partial_phlo_directory(monkeypatch, tmp_path) -> None:
    """Logging-created .phlo directories are not initialized service projects."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".phlo" / "logs").mkdir(parents=True)
    monkeypatch.setattr("phlo_clickstack.cli._require_container_backend", lambda: None)

    result = CliRunner().invoke(clickstack_group, ["query", "SELECT 1"])

    assert result.exit_code != 0
    assert "Phlo services have not been initialized" in result.output
    assert "Missing: .phlo/docker-compose.yml" in result.output
    assert "Run: phlo services init" in result.output
