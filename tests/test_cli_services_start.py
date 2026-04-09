from __future__ import annotations

from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner

from phlo.cli.commands.services.utils import get_profile_service_names
from phlo.plugins.discovery import ServiceDefinition
from tests.helpers import FakeDiscovery, _service


def test_get_profile_service_names_returns_profile_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prometheus = _service("prometheus", profile="observability")
    grafana = _service("grafana", profile="observability")
    loki = _service("loki", profile="observability")
    hasura = _service("hasura", profile="api")
    postgres = _service("postgres", default=True)

    class ProfileFakeDiscovery(FakeDiscovery):
        def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
            all_services = [prometheus, grafana, loki, hasura, postgres]
            return [s for s in all_services if s.profile == profile]

    monkeypatch.setattr(
        "phlo.plugins.discovery.ServiceDiscovery",
        ProfileFakeDiscovery,
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

    class ServiceFakeDiscovery(FakeDiscovery):
        def get_service(self, name: str):
            return service if name == "dagster" else None

    calls: list[list[str]] = []

    def _fake_run_command(cmd, **_kwargs):
        calls.append(list(cmd))
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("phlo.plugins.discovery.ServiceDiscovery", ServiceFakeDiscovery)
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

    class ServiceFakeDiscovery(FakeDiscovery):
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

    monkeypatch.setattr("phlo.plugins.discovery.ServiceDiscovery", ServiceFakeDiscovery)
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

    class ProfilesFakeDiscovery(FakeDiscovery):
        def get_available_profiles(self) -> set[str]:
            return {"api", "observability"}

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("Docker command path should not execute for invalid profiles")

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", ProfilesFakeDiscovery)
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

    class ProfileTargetFakeDiscovery(FakeDiscovery):
        def get_available_profiles(self) -> set[str]:
            return {"observability"}

        def discover(self) -> dict[str, ServiceDefinition]:
            return {"prometheus": _service("prometheus")}

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

    profile_calls: list[tuple[str, ...]] = []
    docker_calls: list[list[str]] = []

    def _fake_get_profile_service_names(profiles: tuple[str, ...]) -> list[str]:
        profile_calls.append(profiles)
        return ["prometheus"]

    def _fake_run_command(cmd: list[str], check=False, capture_output=False) -> CompletedProcess:
        docker_calls.append(cmd)
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", ProfileTargetFakeDiscovery)
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


def test_services_start_includes_setup_companions_for_explicit_targets(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text(
        "services:\n  rustfs: {}\n  rustfs-setup: {}\n  rustfs-volume-setup: {}\n",
    )

    rustfs_volume_setup = _service("rustfs-volume-setup")
    rustfs = _service("rustfs", depends_on=["rustfs-volume-setup"])
    rustfs_setup = _service("rustfs-setup", depends_on=["rustfs"])

    class SetupCompanionFakeDiscovery(FakeDiscovery):
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                rustfs_volume_setup.name: rustfs_volume_setup,
                rustfs.name: rustfs,
                rustfs_setup.name: rustfs_setup,
            }

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            names = {service.name for service in services}
            ordered = [rustfs_volume_setup, rustfs, rustfs_setup]
            return [service for service in ordered if service.name in names]

        def get_available_profiles(self) -> set[str]:
            return set()

    docker_calls: list[list[str]] = []

    def _fake_run_command(cmd: list[str], check=False, capture_output=False) -> CompletedProcess:
        docker_calls.append(cmd)
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", SetupCompanionFakeDiscovery)
    monkeypatch.setattr(start_module, "get_project_name", lambda: "demo-project")
    monkeypatch.setattr(start_module, "compose_base_cmd", lambda **_kwargs: ["docker", "compose"])
    monkeypatch.setattr(start_module, "run_command", _fake_run_command)
    monkeypatch.setattr(start_module, "require_docker", lambda: None)
    monkeypatch.setattr(
        start_module, "_emit_service_lifecycle_events", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(start_module, "_run_service_hooks", lambda *args, **kwargs: None)

    result = CliRunner().invoke(start_module.start_cmd, ["--service", "rustfs"])

    assert result.exit_code == 0
    assert docker_calls
    assert docker_calls[0][-3:] == ["rustfs-volume-setup", "rustfs", "rustfs-setup"]


def test_services_start_rejects_unknown_explicit_targets(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text("services:\n  rustfs: {}\n")

    class RustfsFakeDiscovery(FakeDiscovery):
        def discover(self) -> dict[str, ServiceDefinition]:
            return {"rustfs": _service("rustfs")}

        def get_available_profiles(self) -> set[str]:
            return set()

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", RustfsFakeDiscovery)
    monkeypatch.setattr(start_module, "get_project_name", lambda: "demo-project")

    result = CliRunner().invoke(start_module.start_cmd, ["--service", "rustfs,typo"])

    assert result.exit_code != 0
    assert "Unknown service name(s): typo" in result.output


def test_services_start_requires_full_dependency_match_for_setup_companions(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / "docker-compose.yml").write_text(
        "services:\n  openmetadata-mysql: {}\n  openmetadata-elasticsearch: {}\n"
        "  openmetadata-setup: {}\n",
    )

    mysql = _service("openmetadata-mysql")
    elasticsearch = _service("openmetadata-elasticsearch")
    setup = _service(
        "openmetadata-setup",
        depends_on=["openmetadata-mysql", "openmetadata-elasticsearch"],
    )

    class OpenMetadataFakeDiscovery(FakeDiscovery):
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                mysql.name: mysql,
                elasticsearch.name: elasticsearch,
                setup.name: setup,
            }

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            names = {service.name for service in services}
            ordered = [mysql, elasticsearch, setup]
            return [service for service in ordered if service.name in names]

        def get_available_profiles(self) -> set[str]:
            return set()

    docker_calls: list[list[str]] = []

    def _fake_run_command(cmd: list[str], check=False, capture_output=False) -> CompletedProcess:
        docker_calls.append(cmd)
        return CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(start_module, "ensure_phlo_dir", lambda: phlo_dir)
    monkeypatch.setattr(start_module, "ServiceDiscovery", OpenMetadataFakeDiscovery)
    monkeypatch.setattr(start_module, "get_project_name", lambda: "demo-project")
    monkeypatch.setattr(start_module, "compose_base_cmd", lambda **_kwargs: ["docker", "compose"])
    monkeypatch.setattr(start_module, "run_command", _fake_run_command)
    monkeypatch.setattr(start_module, "require_docker", lambda: None)
    monkeypatch.setattr(
        start_module, "_emit_service_lifecycle_events", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(start_module, "_run_service_hooks", lambda *args, **kwargs: None)

    result = CliRunner().invoke(start_module.start_cmd, ["--service", "openmetadata-mysql"])

    assert result.exit_code == 0
    assert docker_calls
    assert docker_calls[0][-1] == "openmetadata-mysql"
    assert "openmetadata-setup" not in docker_calls[0]


def test_load_native_env_overrides_merges_env_files(tmp_path) -> None:
    from phlo.cli.commands.services import start as start_module

    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env").write_text("PHLO_API_PORT=54000\nOBSERVATORY_PORT=3001\n")
    (phlo_dir / ".env.local").write_text("PHLO_API_PORT=54001\nSECRET_TOKEN='abc123'\n")

    result = start_module._load_native_env_overrides(tmp_path)

    assert result["PHLO_API_PORT"] == "54001"
    assert result["OBSERVATORY_PORT"] == "3001"
    assert result["SECRET_TOKEN"] == "abc123"
