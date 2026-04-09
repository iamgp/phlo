from __future__ import annotations

from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner

from phlo.plugins.discovery import ServiceDefinition
from tests.helpers import FakeDiscovery


def test_extract_compose_service_from_label() -> None:
    from phlo.cli.commands.services.list import _extract_compose_service

    info = {"Labels": "com.docker.compose.project=demo,com.docker.compose.service=postgres,other=x"}
    assert _extract_compose_service(info) == "postgres"


def test_extract_compose_service_returns_none_without_label() -> None:
    from phlo.cli.commands.services.list import _extract_compose_service

    assert _extract_compose_service({"Labels": "some.other.label=val"}) is None
    assert _extract_compose_service({}) is None


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


def test_services_list_handles_malformed_docker_json(
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
        "run_command",
        lambda *_args, **_kwargs: CompletedProcess(["docker", "ps"], 0, "not-valid-json\n", ""),
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(list_module.list_cmd, ["--json"])
    assert result.exit_code == 0
    assert result.output.strip() == "[]"
