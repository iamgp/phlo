from __future__ import annotations

from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner

from phlo.cli.commands.services.utils import get_profile_service_names
from phlo.plugins.discovery import ServiceDefinition


def _service(
    name: str,
    *,
    default: bool = False,
    profile: str | None = None,
    category: str = "core",
) -> ServiceDefinition:
    return ServiceDefinition(
        name=name,
        description=f"{name} service",
        category=category,
        default=default,
        profile=profile,
    )


def test_get_profile_service_names_returns_profile_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prometheus = _service("prometheus", profile="observability")
    grafana = _service("grafana", profile="observability")
    loki = _service("loki", profile="observability")
    hasura = _service("hasura", profile="api")
    postgres = _service("postgres", default=True)

    class FakeDiscovery:
        def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
            all_services = [prometheus, grafana, loki, hasura, postgres]
            return [s for s in all_services if s.profile == profile]

    monkeypatch.setattr(
        "phlo.plugins.discovery.ServiceDiscovery",
        FakeDiscovery,
    )

    result = get_profile_service_names(("observability",))
    assert sorted(result) == ["grafana", "loki", "prometheus"]

    result = get_profile_service_names(("api",))
    assert result == ["hasura"]

    result = get_profile_service_names(("observability", "api"))
    assert sorted(result) == ["grafana", "hasura", "loki", "prometheus"]

    result = get_profile_service_names(())
    assert result == []


def test_run_service_hooks_uses_sys_executable_when_project_venv_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import utils as services_utils

    service = ServiceDefinition(
        name="dagster",
        description="Dagster",
        category="orchestration",
        hooks={"post_start": [{"command": ["python3", "-m", "phlo_dbt.hooks", "compile"]}]},
    )

    class FakeDiscovery:
        def get_service(self, name: str):
            return service if name == "dagster" else None

    calls: list[list[str]] = []

    def _fake_run_command(cmd, **_kwargs):
        calls.append(list(cmd))
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("phlo.plugins.discovery.ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(services_utils, "run_command", _fake_run_command)
    monkeypatch.setattr(services_utils.sys, "executable", "/usr/local/bin/current-python")

    services_utils._run_service_hooks(
        "post_start",
        ["dagster"],
        project_name="demo",
        project_root=tmp_path,
    )

    assert calls
    assert calls[0][0] == "/usr/local/bin/current-python"


def test_run_service_hooks_prefers_project_venv_python(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import utils as services_utils

    service = ServiceDefinition(
        name="dagster",
        description="Dagster",
        category="orchestration",
        hooks={"post_start": [{"command": ["python", "-m", "phlo_dbt.hooks", "compile"]}]},
    )

    class FakeDiscovery:
        def get_service(self, name: str):
            return service if name == "dagster" else None

    calls: list[list[str]] = []

    def _fake_run_command(cmd, **_kwargs):
        calls.append(list(cmd))
        return CompletedProcess(cmd, 0, "", "")

    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("#!/usr/bin/env python3\n")
    venv_python.chmod(0o755)

    monkeypatch.setattr("phlo.plugins.discovery.ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(services_utils, "run_command", _fake_run_command)

    services_utils._run_service_hooks(
        "post_start",
        ["dagster"],
        project_name="demo",
        project_root=tmp_path,
    )

    assert calls
    assert calls[0][0] == str(venv_python)


def test_services_start_rejects_unknown_profile(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text("services:\n  postgres: {}\n")

    class FakeDiscovery:
        def get_available_profiles(self) -> set[str]:
            return {"api", "observability"}

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("Docker command path should not execute for invalid profiles")

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(start_module, "run_command", _unexpected_call)
    monkeypatch.setattr(start_module, "require_docker", _unexpected_call)

    result = CliRunner().invoke(start_module.start_cmd, ["--profile", "not-a-profile"])

    assert result.exit_code != 0
    assert "Invalid profile: not-a-profile." in result.output
    assert "Valid profile options: api, observability" in result.output


def test_services_start_uses_profile_targets_without_default_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text(
        "services:\n  postgres: {}\n  prometheus: {}\n",
    )

    class FakeDiscovery:
        def get_available_profiles(self) -> set[str]:
            return {"observability"}

    profile_calls: list[tuple[str, ...]] = []
    docker_calls: list[list[str]] = []

    def _fake_get_profile_service_names(profiles: tuple[str, ...]) -> list[str]:
        profile_calls.append(profiles)
        return ["prometheus"]

    def _fake_run_command(cmd: list[str], check=False, capture_output=False) -> CompletedProcess:
        docker_calls.append(cmd)
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(start_module, "get_project_name", lambda: "demo-project")
    monkeypatch.setattr(start_module, "get_profile_service_names", _fake_get_profile_service_names)
    monkeypatch.setattr(start_module, "compose_base_cmd", lambda **_kwargs: ["docker", "compose"])
    monkeypatch.setattr(start_module, "run_command", _fake_run_command)
    monkeypatch.setattr(start_module, "require_docker", lambda: None)
    monkeypatch.setattr(
        start_module, "_emit_service_lifecycle_events", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(start_module, "_run_service_hooks", lambda *args, **kwargs: None)

    result = CliRunner().invoke(start_module.start_cmd, ["--profile", "observability"])

    assert result.exit_code == 0
    assert profile_calls == [("observability",)]
    assert docker_calls
    assert "prometheus" in docker_calls[0]
    assert "postgres" not in docker_calls[0]
