"""Tests for Pgweb service plugin."""

from importlib import resources

from phlo_pgweb.plugin import PgwebServicePlugin


def test_pgweb_service_definition():
    """Validate pgweb service metadata in compose definition."""
    plugin = PgwebServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "pgweb"
    assert defn["build"] == {"context": ".", "dockerfile": "pgweb/Dockerfile"}
    assert defn["files"] == [{"source": "Dockerfile", "dest": "pgweb/Dockerfile"}]


def test_pgweb_plugin_metadata():
    """Validate pgweb plugin metadata tags and name."""
    plugin = PgwebServicePlugin()
    meta = plugin.metadata

    assert meta.name == "pgweb"
    assert "postgres" in meta.tags


def test_pgweb_runtime_packages_are_reproducible() -> None:
    dockerfile = resources.files("phlo_pgweb").joinpath("Dockerfile").read_text()

    assert "apk upgrade" not in dockerfile
