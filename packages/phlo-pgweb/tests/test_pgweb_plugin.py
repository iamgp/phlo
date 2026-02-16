"""Tests for Pgweb service plugin."""

from phlo_pgweb.plugin import PgwebServicePlugin


def test_pgweb_service_definition():
    plugin = PgwebServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "pgweb"


def test_pgweb_plugin_metadata():
    plugin = PgwebServicePlugin()
    meta = plugin.metadata

    assert meta.name == "pgweb"
    assert "postgres" in meta.tags
