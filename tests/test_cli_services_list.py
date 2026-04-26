from __future__ import annotations

import pytest
from click.testing import CliRunner

from phlo.cli.infrastructure.container_backend import ContainerInfo
from phlo.plugins.discovery import ServiceDefinition
from tests.helpers import FakeDiscovery


def test_services_list_uses_backend_container_listing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import list as list_module

    class ServiceFakeDiscovery(FakeDiscovery):
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": ServiceDefinition(
                    name="postgres",
                    description="Postgres",
                    category="metadata",
                )
            }

    class FakeBackend:
        name = "podman"

        def list_project_containers(self, project_name: str):
            return [
                ContainerInfo(
                    service="postgres",
                    name=f"{project_name}-postgres-1",
                    state="running",
                    labels={"com.docker.compose.service": "postgres"},
                    ports="0.0.0.0:5432->5432/tcp",
                )
            ]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(list_module, "ServiceDiscovery", ServiceFakeDiscovery)
    monkeypatch.setattr(list_module, "get_project_name", lambda: "demo")
    monkeypatch.setattr(
        list_module, "select_project_container_backend", lambda **_kwargs: FakeBackend()
    )

    result = CliRunner().invoke(list_module.list_cmd, ["--json", "--backend", "podman"])

    assert result.exit_code == 0
    assert '"running": true' in result.output


def test_services_list_wraps_config_parse_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import list as list_module

    (tmp_path / "phlo.yaml").write_text("services: [\n")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(list_module.list_cmd, ["--json"])
    assert result.exit_code == 1
    assert "Failed to read" in result.output
    assert "Check YAML syntax and file permissions" in result.output


def test_services_list_wraps_discovery_failures(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from phlo.cli.commands.services import list as list_module

    class FailingDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            raise RuntimeError("discovery blew up")

    monkeypatch.setattr(list_module, "ServiceDiscovery", FailingDiscovery)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(list_module.list_cmd, ["--json"])
    assert result.exit_code == 1
    assert "Failed to discover services." in result.output
    assert "phlo plugins list" in result.output


def test_services_list_handles_backend_status_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import list as list_module

    class EmptyFakeDiscovery(FakeDiscovery):
        def discover(self) -> dict[str, ServiceDefinition]:
            return {}

    monkeypatch.setattr(list_module, "ServiceDiscovery", EmptyFakeDiscovery)
    monkeypatch.setattr(list_module, "get_project_name", lambda: "demo")
    monkeypatch.setattr(
        list_module,
        "select_project_container_backend",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("bad backend")),
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(list_module.list_cmd, ["--json"])
    assert result.exit_code == 0
    assert result.output.strip() == "[]"
