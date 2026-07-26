"""Tests for Superset service plugin."""

from importlib import resources

from phlo_superset.plugin import SupersetServicePlugin
from phlo_superset.settings import SupersetSettings


def test_superset_service_definition():
    """Verify Superset plugin exposes the expected service name."""
    plugin = SupersetServicePlugin()
    defn = plugin.service_definition

    assert defn["name"] == "superset"


def test_superset_builds_a_patched_runtime_image():
    """The generated service builds the audited runtime derivative."""
    definition = SupersetServicePlugin().service_definition
    dockerfile = resources.files("phlo_superset").joinpath("Dockerfile").read_text()

    assert definition["image"] == "phlo/superset:6.1.0-security-patches"
    assert definition["build"] == {"context": ".", "dockerfile": "superset/Dockerfile"}
    assert definition["compose"]["user"] == "1000:1000"
    assert 'USER "1000"' in dockerfile


def test_superset_plugin_metadata():
    """Verify Superset plugin metadata includes expected identity and tags."""
    plugin = SupersetServicePlugin()
    meta = plugin.metadata

    assert meta.name == "superset"
    assert "bi" in meta.tags


def test_superset_settings_defaults(tmp_path):
    """Verify Superset settings defaults match expected local development values."""
    settings = SupersetSettings(_project_root=tmp_path)

    assert settings.superset_port == 10007
    assert settings.superset_admin_user == "admin"
