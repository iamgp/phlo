from __future__ import annotations

import os
from typing import cast

import pytest
from phlo_dagster.containers import find_dagster_container

from phlo.cli.commands.services.utils import detect_phlo_source_path, get_profile_service_names
from phlo.cli.infrastructure.selection import select_services_to_install
from phlo.plugins.compose.generator import ComposeGenerator
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery


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
    # Mock _resolve_container_name to return the configured name
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "myproj-dagster-webserver-1",
    )

    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda: ["myproj-dagster-webserver-1"],
    )

    assert find_dagster_container("myproj") == "myproj-dagster-webserver-1"


def test_find_dagster_container_falls_back_to_new_name(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock _resolve_container_name to return something that won't match
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )

    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda: ["myproj-dagster-1"],
    )

    assert find_dagster_container("myproj") == "myproj-dagster-1"


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

    # ServiceDiscovery is imported inside get_profile_service_names from phlo.plugins.discovery
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

    detected = detect_phlo_source_path()
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

    detected = detect_phlo_source_path()
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

    generator = ComposeGenerator(cast(ServiceDiscovery, FakeDiscovery()))
    compose = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
        dev_mode=True,
        phlo_src_path="../phlo/src/phlo",
    )

    assert "../phlo/src/phlo/../..:/opt/phlo-dev:rw" in compose
    assert "PHLO_DEV_MODE" in compose
