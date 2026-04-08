from __future__ import annotations

import os
from typing import cast

import pytest
import yaml
from click.testing import CliRunner

from phlo.cli.commands.services.utils import detect_phlo_source_path
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

    assert "/opt/phlo-dev:rw" in compose
    assert "PHLO_DEV_MODE" in compose


def test_compose_generator_passthrough_compose_keys(tmp_path) -> None:
    class FakeDiscovery:
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

        def get_service(self, _name: str) -> None:
            return None

    service = ServiceDefinition(
        name="trino",
        description="trino",
        category="query",
        default=True,
        compose={
            "mem_limit": "3g",
            "cpus": "2.0",
            "ulimits": {"nofile": {"soft": 16384, "hard": 16384}},
        },
    )

    generator = ComposeGenerator(cast(ServiceDiscovery, FakeDiscovery()))
    compose_yaml = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
    )

    data = yaml.safe_load(compose_yaml)
    trino = data["services"]["trino"]
    assert trino["mem_limit"] == "3g"
    assert trino["cpus"] == "2.0"
    assert trino["ulimits"] == {"nofile": {"soft": 16384, "hard": 16384}}


def test_compose_generator_resolves_source_path_dev_volumes(tmp_path) -> None:
    class FakeDiscovery:
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

        def get_service(self, _name: str) -> None:
            return None

    service_source = tmp_path / "packages" / "phlo-observatory"
    service_source.mkdir(parents=True)
    service = ServiceDefinition(
        name="observatory",
        description="observatory",
        category="orchestration",
        default=True,
        source_path=service_source,
        dev={"volumes": ["{source_path}:/app", "/app/node_modules"]},
    )

    generator = ComposeGenerator(cast(ServiceDiscovery, FakeDiscovery()))
    compose_yaml = generator.generate_compose(
        services=[service],
        output_dir=tmp_path / ".phlo",
        dev_mode=True,
        service_dev_mode=True,
    )

    data = yaml.safe_load(compose_yaml)
    observatory = data["services"]["observatory"]
    expected_source = os.path.relpath(service_source, tmp_path / ".phlo")
    assert observatory["volumes"] == [f"{expected_source}:/app", "/app/node_modules"]


def test_services_init_excludes_profile_services_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": _service("postgres", default=True),
                "prometheus": _service("prometheus", profile="observability"),
            }

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

        def get_default_services(self, disabled_services=None) -> list[ServiceDefinition]:
            return [_service("postgres", default=True)]

        def get_available_profiles(self) -> set[str]:
            return {"observability"}

        def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
            if profile == "observability":
                return [_service("prometheus", profile="observability")]
            return []

    class FakeComposer:
        def __init__(self, _discovery):
            pass

        def generate_compose(self, services, output_dir, **_kwargs):
            names = ",".join(sorted(s.name for s in services))
            return f"services: {names}\n"

        def generate_env(self, _services, env_overrides=None):
            return ""

        def generate_env_local(self, _services, env_overrides=None, existing_values=None):
            return ""

        def generate_gitignore(self, _services):
            return ""

        def copy_service_files(self, _services, _output_dir):
            return []

    monkeypatch.chdir(tmp_path)
    from phlo.cli.commands.services import init as init_module

    monkeypatch.setattr(init_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, [])
    assert result.exit_code == 0
    compose = (tmp_path / ".phlo" / "docker-compose.yml").read_text()
    assert "postgres" in compose
    assert "prometheus" not in compose


def test_services_init_includes_requested_profile_services(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": _service("postgres", default=True),
                "prometheus": _service("prometheus", profile="observability"),
            }

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

        def get_default_services(self, disabled_services=None) -> list[ServiceDefinition]:
            return [_service("postgres", default=True)]

        def get_available_profiles(self) -> set[str]:
            return {"observability"}

        def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
            if profile == "observability":
                return [_service("prometheus", profile="observability")]
            return []

    class FakeComposer:
        def __init__(self, _discovery):
            pass

        def generate_compose(self, services, output_dir, **_kwargs):
            names = ",".join(sorted(s.name for s in services))
            return f"services: {names}\n"

        def generate_env(self, _services, env_overrides=None):
            return ""

        def generate_env_local(self, _services, env_overrides=None, existing_values=None):
            return ""

        def generate_gitignore(self, _services):
            return ""

        def copy_service_files(self, _services, _output_dir):
            return []

    monkeypatch.chdir(tmp_path)
    from phlo.cli.commands.services import init as init_module

    monkeypatch.setattr(init_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, ["--profile", "observability"])
    assert result.exit_code == 0
    compose = (tmp_path / ".phlo" / "docker-compose.yml").read_text()
    assert "postgres" in compose
    assert "prometheus" in compose
