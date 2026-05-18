"""Tests for plugin CLI commands."""

import json
import sys

import pytest
from click.testing import CliRunner

from phlo.cli.commands.plugin import plugin_group
from phlo.plugins import (
    PluginMetadata,
    QualityCheckPlugin,
    ServicePlugin,
    SourceConnectorPlugin,
    TransformationPlugin,
)
from phlo.plugins.base import (
    CliCommandPlugin,
    IngestionProviderPlugin,
    QualityProviderPlugin,
    TransformationProviderPlugin,
)
from phlo.plugins.discovery import get_global_registry
from phlo.plugins.registry_client import RegistryPlugin


class DummySource(SourceConnectorPlugin):
    """Stub source connector for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Metadata for the dummy source plugin.
        """
        return PluginMetadata(name="dummy_source", version="1.0.0")

    def fetch_data(self, config):
        """Yield a single dummy record.

        Args:
            config: Source configuration.

        Yields:
            dict: Dummy source row.
        """
        yield {"id": 1}


class DummyQuality(QualityCheckPlugin):
    """Stub quality plugin for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Metadata for the dummy quality plugin.
        """
        return PluginMetadata(name="dummy_quality", version="1.0.0")

    def create_check(self, **kwargs):
        """Create a no-op quality check.

        Args:
            **kwargs: Quality check options.

        Returns:
            None: No check object for this stub.
        """
        return


class DummyTransform(TransformationPlugin):
    """Stub transform plugin for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Metadata for the dummy transform plugin.
        """
        return PluginMetadata(name="dummy_transform", version="1.0.0")

    def transform(self, df, config):
        """Return input data unchanged.

        Args:
            df: Input dataframe-like object.
            config: Transform configuration.

        Returns:
            Any: Unmodified input dataframe-like object.
        """
        return df


class DummyService(ServicePlugin):
    """Stub service plugin for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata: Metadata for the dummy service plugin.
        """
        return PluginMetadata(name="dummy_service", version="1.0.0")

    @property
    def service_definition(self) -> dict:
        """Return a minimal service definition.

        Returns:
            dict: Service category and compose configuration.
        """
        return {"category": "core", "compose": {"image": "dummy:latest"}}


class DummyIngestionProvider(IngestionProviderPlugin):
    """Stub ingestion provider for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_ingestion", version="1.0.0")

    def get_decorator(self):
        return lambda fn=None, **_kwargs: fn

    def get_asset_retriever(self):
        return list


class DummyQualityProvider(QualityProviderPlugin):
    """Stub quality provider for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_quality_provider", version="1.0.0")

    def get_decorator(self):
        return lambda fn=None, **_kwargs: fn

    def get_check_classes(self) -> dict[str, type]:
        return {}


class DummyTransformationProvider(TransformationProviderPlugin):
    """Stub transformation provider for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_transformation_provider", version="1.0.0")

    def get_asset_retriever(self):
        return list


class DummyCliCommand(CliCommandPlugin):
    """Stub CLI command plugin for CLI plugin tests."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="dummy_cli", version="1.0.0")

    def get_cli_commands(self):
        return []


@pytest.fixture
def setup_registry():
    """Provide an isolated plugin registry for each test.

    Yields:
        PluginRegistry: Cleared global registry with dummy plugins registered.
    """
    registry = get_global_registry()
    registry.clear()
    registry.register_source_connector(DummySource(), replace=True)
    registry.register_quality_check(DummyQuality(), replace=True)
    registry.register_transformation(DummyTransform(), replace=True)
    registry.register_service(DummyService(), replace=True)
    yield registry
    registry.clear()


def test_plugin_list_json_installed(setup_registry):
    """List command returns installed plugins as JSON."""
    # #given
    runner = CliRunner()

    # #when
    result = runner.invoke(plugin_group, ["list", "--json"])

    # #then
    data = json.loads(result.output)
    types = {plugin["type"] for plugin in data["installed"]}
    assert result.exit_code == 0
    assert types >= {"source", "quality", "transform", "service"}
    assert {plugin["name"] for plugin in data["installed"]} >= {
        "dummy_source",
        "dummy_quality",
        "dummy_transform",
        "dummy_service",
    }


def test_plugin_list_accepts_singular_type_alias(setup_registry):
    """List accepts the same singular aliases as plugin create."""
    result = CliRunner().invoke(plugin_group, ["list", "--type", "source", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert [plugin["name"] for plugin in data["installed"]] == ["dummy_source"]


def test_plugin_list_accepts_provider_and_cli_type_aliases(setup_registry):
    """List can filter plugin categories that are shown in all-plugin output."""
    registry = setup_registry
    registry.register_ingestion_provider(DummyIngestionProvider(), replace=True)
    registry.register_quality_provider(DummyQualityProvider(), replace=True)
    registry.register_transformation_provider(DummyTransformationProvider(), replace=True)
    registry.register_cli_command_plugin(DummyCliCommand(), replace=True)

    runner = CliRunner()

    ingestion = runner.invoke(plugin_group, ["list", "--type", "ingestion", "--json"])
    quality_provider = runner.invoke(plugin_group, ["list", "--type", "quality-provider", "--json"])
    transformation_provider = runner.invoke(
        plugin_group, ["list", "--type", "transformation-provider", "--json"]
    )
    cli = runner.invoke(plugin_group, ["list", "--type", "cli", "--json"])

    assert ingestion.exit_code == 0
    assert quality_provider.exit_code == 0
    assert transformation_provider.exit_code == 0
    assert cli.exit_code == 0
    assert json.loads(ingestion.output)["installed"][0]["type"] == "ingestion_provider"
    assert json.loads(quality_provider.output)["installed"][0]["type"] == "quality_provider"
    assert (
        json.loads(transformation_provider.output)["installed"][0]["type"]
        == "transformation_provider"
    )
    assert json.loads(cli.output)["installed"][0]["type"] == "cli"


def test_plugin_info_resolves_phlo_distribution_alias(setup_registry):
    """Info resolves common package-style names such as phlo-trino."""
    result = CliRunner().invoke(plugin_group, ["info", "phlo-dummy-source", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "dummy_source"


def test_plugin_check_json_emits_only_json(setup_registry):
    """Check --json stdout is parseable JSON without prose prefixes."""
    result = CliRunner().invoke(plugin_group, ["check", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "valid" in data
    assert "invalid" in data


def test_plugin_list_all_json(setup_registry, monkeypatch):
    """List command includes registry plugins when --all is set."""
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

    def mock_collect_registry_plugins(plugin_type: str) -> list[dict]:
        """Convert mocked registry plugins to CLI payload dictionaries.

        Args:
            plugin_type: Requested plugin type.

        Returns:
            list[dict]: Serialized registry plugins for the CLI response.
        """
        from phlo.cli.commands.plugin.utils import registry_plugin_to_dict

        return [registry_plugin_to_dict(p) for p in registry_plugins]

    monkeypatch.setattr(
        "phlo.cli.commands.plugin.list.collect_registry_plugins",
        mock_collect_registry_plugins,
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
        "phlo.cli.commands.plugin.search.search_plugins",
        lambda query, plugin_type, tags: registry_plugins,
    )

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["search", "service", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["name"] == "registry_service"


def test_plugin_search_includes_installed_plugins(monkeypatch, setup_registry):
    """Search should not hide installed plugins when registry results are sparse."""
    monkeypatch.setattr("phlo.cli.commands.plugin.search.search_plugins", lambda *_args, **_kw: [])

    result = CliRunner().invoke(plugin_group, ["search", "dummy", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert {item["name"] for item in data} >= {
        "dummy_source",
        "dummy_quality",
        "dummy_transform",
        "dummy_service",
    }


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
        "phlo.cli.commands.plugin.install.get_registry_plugin",
        lambda name: registry_plugin,
    )
    monkeypatch.setattr("phlo.cli.commands.plugin.install.run_pip", lambda args: calls.append(args))

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
        "phlo.cli.commands.plugin.update.list_registry_plugins",
        lambda: registry_plugins,
    )
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.get_installed_version",
        lambda package: "1.0.0",
    )
    monkeypatch.setattr("phlo.cli.commands.plugin.update.run_pip", lambda args: calls.append(args))

    runner = CliRunner()
    result = runner.invoke(plugin_group, ["update"])

    assert result.exit_code == 0
    assert calls == [["install", "--upgrade", "phlo-plugin-registry==2.0.0"]]


def test_run_pip_prefers_uv_when_available(monkeypatch):
    """Use `uv pip` when uv is available."""
    from phlo.cli.commands.plugin.utils import run_pip

    calls: list[tuple[list[str], bool, float]] = []

    monkeypatch.setattr("phlo.cli.commands.plugin.utils.shutil.which", lambda _: "/usr/bin/uv")
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.importlib.util.find_spec", lambda _: object()
    )
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.subprocess.run",
        lambda cmd, check, timeout: calls.append((cmd, check, timeout)),
    )

    run_pip(["install", "demo-plugin"], timeout=12)

    assert calls == [(["uv", "pip", "install", "demo-plugin"], True, 12)]


def test_run_pip_uses_python_pip_when_uv_missing(monkeypatch):
    """Use `python -m pip` when uv is unavailable and pip is importable."""
    from phlo.cli.commands.plugin.utils import run_pip

    calls: list[tuple[list[str], bool, float]] = []

    monkeypatch.setattr("phlo.cli.commands.plugin.utils.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.importlib.util.find_spec", lambda _: object()
    )
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.subprocess.run",
        lambda cmd, check, timeout: calls.append((cmd, check, timeout)),
    )

    run_pip(["install", "demo-plugin"], timeout=12)

    assert calls == [([sys.executable, "-m", "pip", "install", "demo-plugin"], True, 12)]


def test_run_pip_uses_uv_when_pip_module_missing(monkeypatch):
    """Use `uv pip` when pip module is unavailable but `uv` exists."""
    from phlo.cli.commands.plugin.utils import run_pip

    calls: list[tuple[list[str], bool, float]] = []

    monkeypatch.setattr("phlo.cli.commands.plugin.utils.importlib.util.find_spec", lambda _: None)
    monkeypatch.setattr("phlo.cli.commands.plugin.utils.shutil.which", lambda _: "/usr/bin/uv")
    monkeypatch.setattr(
        "phlo.cli.commands.plugin.utils.subprocess.run",
        lambda cmd, check, timeout: calls.append((cmd, check, timeout)),
    )

    run_pip(["install", "demo-plugin"], timeout=9)

    assert calls == [(["uv", "pip", "install", "demo-plugin"], True, 9)]


def test_run_pip_errors_when_no_pip_and_no_uv(monkeypatch):
    """Raise runtime error when neither pip module nor `uv` is available."""
    from phlo.cli.commands.plugin.utils import run_pip

    monkeypatch.setattr("phlo.cli.commands.plugin.utils.importlib.util.find_spec", lambda _: None)
    monkeypatch.setattr("phlo.cli.commands.plugin.utils.shutil.which", lambda _: None)

    with pytest.raises(RuntimeError, match="pip module is unavailable"):
        run_pip(["install", "demo-plugin"])


def test_normalize_plugin_type_reports_unknown_type() -> None:
    """Internal callers get a clear error for unmapped plugin types."""
    from phlo.cli.commands.plugin.utils import normalize_plugin_type

    with pytest.raises(ValueError, match="Unknown plugin type: nope"):
        normalize_plugin_type("nope")
