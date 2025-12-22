"""Tests for plugin CLI commands."""

import json

from click.testing import CliRunner

from phlo.cli.plugin import plugin_group
from phlo.plugins import (
    PluginMetadata,
    QualityCheckPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.registry import get_global_registry
from phlo.plugins.registry_client import RegistryPlugin


class DummySource(SourceConnectorPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_source", version="1.0.0")

    def fetch_data(self, config):
        yield {"id": 1}


class DummyQuality(QualityCheckPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_quality", version="1.0.0")

    def create_check(self, **kwargs):
        return None


class DummyTransform(TransformationPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_transform", version="1.0.0")

    def transform(self, df, config):
        return df


class DummyService(ServicePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_service", version="1.0.0")

    @property
    def service_definition(self) -> dict:
        return {"category": "core", "compose": {"image": "dummy:latest"}}


def _setup_registry():
    registry = get_global_registry()
    registry.clear()
    registry.register_source_connector(DummySource(), replace=True)
    registry.register_quality_check(DummyQuality(), replace=True)
    registry.register_transformation(DummyTransform(), replace=True)
    registry.register_service(DummyService(), replace=True)
    return registry


def test_plugin_list_json_installed():
    """List command returns installed plugins as JSON."""
    _setup_registry()

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["list", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    types = {plugin["type"] for plugin in data}
    assert "source" in types
    assert "quality" in types
    assert "transform" in types
    assert "service" in types


def test_plugin_list_all_json(monkeypatch):
    """List command includes registry plugins when --all is set."""
    _setup_registry()
    registry_plugins = [
        RegistryPlugin(
            name="registry_source",
            type="source",
            package="phlo-plugin-registry",
            version="1.2.3",
            description="Registry plugin",
            author="Phlo Team",
            homepage=None,
            tags=["example"],
            verified=True,
            core=False,
        )
    ]

    monkeypatch.setattr(
        "phlo.cli.plugin.list_registry_plugins",
        lambda: registry_plugins,
    )

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["list", "--all", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "installed" in data
    assert "available" in data
    assert data["available"][0]["name"] == "registry_source"


def test_plugin_search(monkeypatch):
    """Search command returns registry plugins."""
    registry_plugins = [
        RegistryPlugin(
            name="registry_service",
            type="service",
            package="phlo-plugin-service",
            version="1.0.0",
            description="Service plugin",
            author="Phlo Team",
            homepage=None,
            tags=["service"],
            verified=True,
            core=False,
        )
    ]

    monkeypatch.setattr(
        "phlo.cli.plugin.search_plugins",
        lambda query, plugin_type, tags: registry_plugins,
    )

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["search", "service", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["name"] == "registry_service"


def test_plugin_install(monkeypatch):
    """Install command resolves registry name and calls pip."""
    registry_plugin = RegistryPlugin(
        name="registry_source",
        type="source",
        package="phlo-plugin-registry",
        version="1.0.0",
        description="Registry plugin",
        author="Phlo Team",
        homepage=None,
        tags=["example"],
        verified=True,
        core=False,
    )
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "phlo.cli.plugin.get_registry_plugin",
        lambda name: registry_plugin,
    )
    monkeypatch.setattr("phlo.cli.plugin._run_pip", lambda args: calls.append(args))

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["install", "registry_source"])

    assert result.exit_code == 0
    assert calls == [["install", "phlo-plugin-registry==1.0.0"]]


def test_plugin_update(monkeypatch):
    """Update command upgrades installed plugins."""
    registry_plugins = [
        RegistryPlugin(
            name="registry_source",
            type="source",
            package="phlo-plugin-registry",
            version="2.0.0",
            description="Registry plugin",
            author="Phlo Team",
            homepage=None,
            tags=["example"],
            verified=True,
            core=False,
        )
    ]
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "phlo.cli.plugin.list_registry_plugins",
        lambda: registry_plugins,
    )
    monkeypatch.setattr(
        "phlo.cli.plugin._get_installed_version",
        lambda package: "1.0.0",
    )
    monkeypatch.setattr("phlo.cli.plugin._run_pip", lambda args: calls.append(args))

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["update"])

    assert result.exit_code == 0
    assert calls == [["install", "--upgrade", "phlo-plugin-registry==2.0.0"]]
