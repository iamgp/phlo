"""Tests for plugin CLI commands."""

import json
import sys

import pytest
from click.testing import CliRunner

from phlo.cli.commands.plugin import plugin_group
from phlo.plugins import PluginMetadata
from phlo.plugins.base import (
    CliCommandPlugin,
    IngestionProviderPlugin,
    QualityProviderPlugin,
    TransformationProviderPlugin,
)
from phlo.plugins.discovery import get_global_registry
from phlo.plugins.registry_client import RegistryPlugin
from tests.helpers import (
    DummyQualityPlugin as DummyQuality,
)
from tests.helpers import (
    DummyServicePlugin as DummyService,
)
from tests.helpers import (
    DummySourcePlugin as DummySource,
)
from tests.helpers import (
    DummyTransformPlugin as DummyTransform,
)


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
    registry.register("source_connector", DummySource(), replace=True)
    registry.register("quality_check", DummyQuality(), replace=True)
    registry.register("transformation", DummyTransform(), replace=True)
    registry.register("service", DummyService(), replace=True)
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
    registry.register("ingestion_provider", DummyIngestionProvider(), replace=True)
    registry.register("quality_provider", DummyQualityProvider(), replace=True)
    registry.register("transformation_provider", DummyTransformationProvider(), replace=True)
    registry.register("cli_command", DummyCliCommand(), replace=True)

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


def test_plugin_check_containers_checks_generated_project(monkeypatch, setup_registry, tmp_path):
    """Container checks run tools against files generated in an external project."""
    from phlo.cli.commands.plugin import check as check_module

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == "/bin/phlo":
            project = kwargs["cwd"]
            dockerfile = project / ".phlo" / "dagster" / "Dockerfile"
            dockerfile.parent.mkdir(parents=True, exist_ok=True)
            dockerfile.write_text("FROM python:3.11\n")
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(check_module.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(check_module.subprocess, "run", fake_run)
    monkeypatch.setattr(check_module, "discover_plugins", lambda **_: {"service": []})
    monkeypatch.setattr(check_module, "validate_plugins", lambda: {"valid": [], "invalid": []})

    result = check_module.check_generated_containers(
        project_parent=tmp_path,
        service_files={"dagster/Dockerfile": "phlo-dagster"},
        service_names=["phlo-api", "observatory"],
    )

    assert result["dockerfiles"] == ["dagster/Dockerfile"]
    assert result["owners"] == {"dagster/Dockerfile": "phlo-dagster"}
    assert calls[0][0][0] == "/bin/phlo"
    assert calls[1][0] == [
        "/bin/phlo",
        "services",
        "add",
        "--service",
        "phlo-api",
        "--service",
        "observatory",
        "--no-start",
    ]
    generated_dockerfile = calls[0][1]["cwd"] / ".phlo" / "dagster" / "Dockerfile"
    assert calls[2][0] == ["/bin/hadolint", str(generated_dockerfile)]
    assert calls[3][0][:5] == ["/bin/trivy", "config", "--exit-code", "1", "--severity"]


def test_plugin_check_containers_reports_tool_failure(monkeypatch, tmp_path):
    """A generated-container tool failure is reported as a CLI failure."""
    from phlo.cli.commands.plugin import check as check_module

    def fake_run(command, **kwargs):
        return type("Result", (), {"returncode": 1, "stdout": "bad", "stderr": "failure"})()

    monkeypatch.setattr(check_module.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(check_module.subprocess, "run", fake_run)

    with pytest.raises(check_module.ContainerCheckError, match="phlo services init failed"):
        check_module.check_generated_containers(
            project_parent=tmp_path,
            service_files={"dagster/Dockerfile": "phlo-dagster"},
        )


def test_plugin_check_containers_rejects_unowned_dockerfile(monkeypatch, tmp_path):
    """Generated Dockerfiles without discovered package ownership fail closed."""
    from phlo.cli.commands.plugin import check as check_module

    def fake_run(command, **kwargs):
        dockerfile = kwargs["cwd"] / ".phlo" / "unknown" / "Dockerfile"
        dockerfile.parent.mkdir(parents=True, exist_ok=True)
        dockerfile.write_text("FROM python:3.11\n")
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(check_module.shutil, "which", lambda name: f"/bin/{name}")

    with pytest.raises(check_module.ContainerCheckError, match="no package owner"):
        check_module.check_generated_containers(
            project_parent=tmp_path,
            service_files={},
            command_runner=fake_run,
        )


def test_plugin_check_containers_reports_all_package_failures(monkeypatch, tmp_path):
    """All generated package failures are reported after every scanner runs."""
    from phlo.cli.commands.plugin import check as check_module

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "/bin/phlo":
            for name in ("one", "two"):
                dockerfile = kwargs["cwd"] / ".phlo" / name / "Dockerfile"
                dockerfile.parent.mkdir(parents=True, exist_ok=True)
                dockerfile.write_text("FROM python:3.11\n")
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return type("Result", (), {"returncode": 1, "stdout": "", "stderr": "failed"})()

    monkeypatch.setattr(check_module.shutil, "which", lambda name: f"/bin/{name}")

    with pytest.raises(check_module.ContainerCheckError) as exc_info:
        check_module.check_generated_containers(
            project_parent=tmp_path,
            service_files={"one/Dockerfile": "package-one", "two/Dockerfile": "package-two"},
            command_runner=fake_run,
        )

    message = str(exc_info.value)
    assert "package-one" in message
    assert "package-two" in message
    assert "trivy [project]" in message
    assert [command[0] for command in calls] == [
        "/bin/phlo",
        "/bin/hadolint",
        "/bin/hadolint",
        "/bin/trivy",
    ]


def test_plugin_check_containers_is_available_at_public_cli_seam(monkeypatch, setup_registry):
    """The public check command exposes generated-container results as JSON."""
    from phlo.cli.commands.plugin import check as check_module

    monkeypatch.setattr(
        check_module,
        "check_generated_containers",
        lambda: {
            "dockerfiles": ["dagster/Dockerfile"],
            "owners": {"dagster/Dockerfile": "phlo-dagster"},
        },
    )

    result = CliRunner().invoke(plugin_group, ["check", "--containers", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.output)["containers"]["owners"] == {
        "dagster/Dockerfile": "phlo-dagster"
    }


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
