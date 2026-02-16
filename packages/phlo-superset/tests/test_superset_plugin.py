"""Tests for Superset service plugin."""

from phlo_superset.plugin import SupersetServicePlugin
from phlo_superset.settings import SupersetSettings


def test_superset_service_definition():
    plugin = SupersetServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "superset"


def test_superset_plugin_metadata():
    plugin = SupersetServicePlugin()
    meta = plugin.metadata

    assert meta.name == "superset"
    assert "bi" in meta.tags


def test_superset_settings_defaults():
    settings = SupersetSettings()

    assert settings.superset_port == 10007
    assert settings.superset_admin_user == "admin"
