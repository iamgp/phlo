from __future__ import annotations

import os
from subprocess import CompletedProcess

import pytest

import phlo.cli.services as services_cli
from phlo.cli._services.selection import select_services_to_install
from phlo.services.composer import ComposeGenerator
from phlo.services.discovery import ServiceDefinition


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


def test_select_services_to_install_respects_enabled_disabled_and_profiles() -> None:
    postgres = _service("postgres", default=True)
    minio = _service("minio", default=True)
    prometheus = _service("prometheus", profile="observability")
    grafana = _service("grafana", profile="observability")

    all_services = {s.name: s for s in [postgres, minio, prometheus, grafana]}
    default_services = [postgres, minio]

    services_to_install = select_services_to_install(
        all_services=all_services,
        default_services=default_services,
        enabled_names=["prometheus"],
        disabled_names=["minio"],
    )

    assert [s.name for s in services_to_install] == ["postgres", "prometheus", "grafana"]


def test_find_dagster_container_prefers_configured_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "phlo.infrastructure.get_container_name",
        lambda service, project: "myproj-dagster-webserver-1",
    )

    def fake_run_command(cmd, **_kwargs):
        assert cmd[:3] == ["docker", "ps", "--format"]
        return CompletedProcess(cmd, 0, stdout="myproj-dagster-webserver-1\n", stderr="")

    monkeypatch.setattr(services_cli, "run_command", fake_run_command)

    assert services_cli.find_dagster_container("myproj") == "myproj-dagster-webserver-1"


def test_find_dagster_container_falls_back_to_new_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("phlo.infrastructure.get_container_name", lambda service, project: "cfg")

    def fake_run_command(cmd, **_kwargs):
        return CompletedProcess(cmd, 0, stdout="myproj-dagster-1\n", stderr="")

    monkeypatch.setattr(services_cli, "run_command", fake_run_command)

    assert services_cli.find_dagster_container("myproj") == "myproj-dagster-1"


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

    # ServiceDiscovery is imported inside get_profile_service_names from phlo.services
    monkeypatch.setattr(
        "phlo.services.ServiceDiscovery",
        FakeDiscovery,
    )

    result = services_cli.get_profile_service_names(("observability",))
    assert sorted(result) == ["grafana", "loki", "prometheus"]

    result = services_cli.get_profile_service_names(("api",))
    assert result == ["hasura"]

    result = services_cli.get_profile_service_names(("observability", "api"))
    assert sorted(result) == ["grafana", "hasura", "loki", "prometheus"]

    result = services_cli.get_profile_service_names(())
    assert result == []


def test_detect_phlo_source_path_finds_sibling_phlo_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    phlo_repo = tmp_path / "phlo"
    package_dir = phlo_repo / "src" / "phlo"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("")

    project_dir = tmp_path / "pokemon-lakehouse"
    project_dir.mkdir()

    monkeypatch.chdir(project_dir)
    monkeypatch.delenv("PHLO_DEV_SOURCE", raising=False)

    detected = services_cli.detect_phlo_source_path()
    expected = os.path.relpath(package_dir, project_dir / ".phlo")
    assert detected == expected


def test_detect_phlo_source_path_accepts_repo_root_in_env_var(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    phlo_repo = tmp_path / "phlo"
    package_dir = phlo_repo / "src" / "phlo"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("")

    project_dir = tmp_path / "pokemon-lakehouse"
    project_dir.mkdir()

    monkeypatch.chdir(project_dir)
    monkeypatch.setenv("PHLO_DEV_SOURCE", str(phlo_repo))

    detected = services_cli.detect_phlo_source_path()
    expected = os.path.relpath(package_dir, project_dir / ".phlo")
    assert detected == expected


def test_compose_generator_injects_phlo_dev_mounts(tmp_path) -> None:
    class FakeDiscovery:
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

        def get_service(self, _name: str) -> None:
            return None

    service = ServiceDefinition(
        name="dagster",
        description="dagster",
        category="orchestration",
        default=True,
        phlo_dev=True,
        compose={},
    )

    generator = ComposeGenerator(FakeDiscovery())
    compose = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
        dev_mode=True,
        phlo_src_path="../phlo/src/phlo",
    )

    assert "../phlo/src/phlo/../..:/opt/phlo-dev:rw" in compose
    assert "PHLO_DEV_MODE" in compose
