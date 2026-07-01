from __future__ import annotations

import os
import re
from typing import cast

import pytest
import yaml
from click.testing import CliRunner

from phlo.cli.commands.services.utils import detect_phlo_source_path
from phlo.cli.infrastructure.selection import select_services_to_install
from phlo.plugins.compose.env import generate_env, generate_env_local
from phlo.plugins.compose.generator import ComposeGenerator
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery
from tests.helpers import FakeDiscovery, _service


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
    class MinimalFakeDiscovery(FakeDiscovery):
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

    service = ServiceDefinition(
        name="dagster",
        description="dagster",
        category="orchestration",
        default=True,
        phlo_dev=True,
        compose={},
    )

    generator = ComposeGenerator(cast(ServiceDiscovery, MinimalFakeDiscovery()))
    compose = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
        dev_mode=True,
        phlo_src_path="../phlo/src/phlo",
    )

    assert "/opt/phlo-dev:rw" in compose
    assert "PHLO_DEV_MODE" in compose


def test_compose_generator_passthrough_compose_keys(tmp_path) -> None:
    class MinimalFakeDiscovery(FakeDiscovery):
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

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

    generator = ComposeGenerator(cast(ServiceDiscovery, MinimalFakeDiscovery()))
    compose_yaml = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
    )

    data = yaml.safe_load(compose_yaml)
    trino = data["services"]["trino"]
    assert trino["mem_limit"] == "3g"
    assert trino["cpus"] == "2.0"
    assert trino["ulimits"] == {"nofile": {"soft": 16384, "hard": 16384}}


def test_compose_generator_declares_named_volumes(tmp_path) -> None:
    class MinimalFakeDiscovery(FakeDiscovery):
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

    service = ServiceDefinition(
        name="postgres",
        description="postgres",
        category="core",
        default=True,
        compose={"volumes": ["postgres-data:/var/lib/postgresql/data", "./logs:/logs"]},
    )

    generator = ComposeGenerator(cast(ServiceDiscovery, MinimalFakeDiscovery()))
    compose_yaml = generator.generate_compose(
        services=[service],
        output_dir=tmp_path,
    )

    data = yaml.safe_load(compose_yaml)
    assert data["volumes"] == {"postgres-data": {}}


def test_generate_env_pins_package_versions_for_service_builds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keeps repeated service builds on the installed Phlo version, not Docker's stale latest."""
    versions = {"phlo": "9.8.7", "phlo-api": "3.2.1"}
    monkeypatch.setattr("phlo.plugins.compose.env.version", versions.__getitem__)
    service = ServiceDefinition(
        name="phlo-api",
        description="api",
        category="api",
        default=True,
        env_vars={
            "PHLO_VERSION": {
                "default": "",
                "package": "phlo",
                "description": "Phlo version to install",
            },
            "PHLO_API_VERSION": {
                "default": "",
                "package": "phlo-api",
                "description": "phlo-api version to install",
            },
        },
    )

    env = generate_env([service])

    assert "PHLO_VERSION=9.8.7" in env
    assert "PHLO_API_VERSION=3.2.1" in env


def test_generate_env_local_keeps_known_non_secret_values_out_of_local_overrides() -> None:
    service = ServiceDefinition(
        name="postgres",
        description="postgres",
        category="core",
        default=True,
        env_vars={
            "POSTGRES_PORT": {
                "default": "5432",
                "description": "Postgres port",
            },
            "POSTGRES_PASSWORD": {
                "default": "postgres",
                "description": "Postgres password",
                "secret": True,
            },
        },
    )

    env_local = generate_env_local(
        [service],
        existing_values={
            "POSTGRES_PORT": "15432",
            "POSTGRES_PASSWORD": "secret",
            "CUSTOM_LOCAL": "kept",
        },
    )

    assert "POSTGRES_PASSWORD=secret" in env_local
    assert "CUSTOM_LOCAL=kept" in env_local
    assert "POSTGRES_PORT=15432" not in env_local


def test_generate_env_local_generates_new_secret_values() -> None:
    service = ServiceDefinition(
        name="postgres",
        description="postgres",
        category="core",
        default=True,
        env_vars={
            "POSTGRES_PASSWORD": {
                "default": "postgres",
                "description": "Postgres password",
                "secret": True,
            },
        },
    )

    env_local = generate_env_local([service])

    assert "POSTGRES_PASSWORD=postgres" not in env_local
    assert re.search(r"POSTGRES_PASSWORD=phlo_[A-Za-z0-9_-]{32,}", env_local)


def test_generate_env_local_uses_s3_safe_minio_root_password() -> None:
    service = ServiceDefinition(
        name="minio",
        description="minio",
        category="core",
        default=True,
        env_vars={
            "MINIO_ROOT_PASSWORD": {
                "default": "minio123",
                "description": "MinIO root password",
                "secret": True,
            },
        },
    )

    env_local = generate_env_local([service])

    assert "MINIO_ROOT_PASSWORD=minio123" not in env_local
    assert re.search(r"MINIO_ROOT_PASSWORD=[a-f0-9]{40}\n", env_local)


def test_generate_env_local_preserves_existing_secret_values() -> None:
    service = ServiceDefinition(
        name="postgres",
        description="postgres",
        category="core",
        default=True,
        env_vars={
            "POSTGRES_PASSWORD": {
                "default": "postgres",
                "description": "Postgres password",
                "secret": True,
            },
        },
    )

    env_local = generate_env_local(
        [service],
        existing_values={"POSTGRES_PASSWORD": "existing-secret"},
    )

    assert "POSTGRES_PASSWORD=existing-secret" in env_local


def test_compose_generator_resolves_source_path_dev_volumes(tmp_path) -> None:
    class MinimalFakeDiscovery(FakeDiscovery):
        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            return services

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

    generator = ComposeGenerator(cast(ServiceDiscovery, MinimalFakeDiscovery()))
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
    postgres = _service("postgres", default=True)
    prometheus = _service("prometheus", profile="observability")
    fake_discovery = FakeDiscovery(
        {postgres.name: postgres, prometheus.name: prometheus},
        default_names=(postgres.name,),
    )

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

    monkeypatch.setattr(init_module, "ServiceDiscovery", lambda: fake_discovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, [])
    assert result.exit_code == 0
    compose = (tmp_path / ".phlo" / "docker-compose.yml").read_text()
    assert "postgres" in compose
    assert "prometheus" not in compose


def test_services_init_reports_malformed_phlo_yaml_without_traceback(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    (tmp_path / "phlo.yaml").write_text("name: [unterminated\n")
    monkeypatch.chdir(tmp_path)

    from phlo.cli.commands.services import init as init_module

    result = CliRunner().invoke(init_module.init_cmd, ["--force", "--no-dev"])

    assert result.exit_code == 1
    assert "invalid phlo.yaml" in result.output
    assert "Traceback" not in result.output
    assert not isinstance(result.exception, yaml.YAMLError)


def test_services_init_allows_logs_only_phlo_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """A fresh `phlo init` can create .phlo/logs before infrastructure is rendered."""
    postgres = _service("postgres", default=True)
    fake_discovery = FakeDiscovery({postgres.name: postgres}, default_names=(postgres.name,))

    class FakeComposer:
        def __init__(self, _discovery):
            pass

        def generate_compose(self, services, output_dir, **_kwargs):
            return "services: {}\n"

        def generate_env(self, _services, env_overrides=None):
            return ""

        def generate_env_local(self, _services, env_overrides=None, existing_values=None):
            return ""

        def generate_gitignore(self, _services):
            return ""

        def copy_service_files(self, _services, _output_dir):
            return []

    (tmp_path / ".phlo" / "logs").mkdir(parents=True)
    (tmp_path / ".phlo" / "logs" / "20260503.log").write_text("{}\n")
    monkeypatch.chdir(tmp_path)
    from phlo.cli.commands.services import init as init_module

    monkeypatch.setattr(init_module, "ServiceDiscovery", lambda: fake_discovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, [])

    assert result.exit_code == 0
    assert (tmp_path / ".phlo" / "docker-compose.yml").exists()


def test_services_init_includes_requested_profile_services(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    postgres = _service("postgres", default=True)
    prometheus = _service("prometheus", profile="observability")
    fake_discovery = FakeDiscovery(
        {postgres.name: postgres, prometheus.name: prometheus},
        default_names=(postgres.name,),
    )

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

    monkeypatch.setattr(init_module, "ServiceDiscovery", lambda: fake_discovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, ["--profile", "observability"])
    assert result.exit_code == 0
    compose = (tmp_path / ".phlo" / "docker-compose.yml").read_text()
    assert "postgres" in compose
    assert "prometheus" in compose


def test_services_init_uses_lifecycle_planner_for_profiles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    postgres = _service("postgres", default=True)
    grafana = _service("grafana", profile="observability")
    fake_discovery = FakeDiscovery(
        {postgres.name: postgres, grafana.name: grafana},
        default_names=(postgres.name,),
    )
    copied: list[str] = []

    class FakeComposer:
        def __init__(self, _discovery):
            pass

        def generate_compose(self, selected, *_args, **_kwargs):
            copied.extend(service.name for service in selected)
            return "services: {}\n"

        def generate_env(self, _services, env_overrides=None):
            return ""

        def generate_env_local(self, _services, env_overrides=None, existing_values=None):
            return ""

        def generate_gitignore(self, _services):
            return ""

        def copy_service_files(self, *_args, **_kwargs):
            return []

    monkeypatch.chdir(tmp_path)
    from phlo.cli.commands.services import init as init_module

    monkeypatch.setattr(init_module, "ServiceDiscovery", lambda: fake_discovery)
    monkeypatch.setattr(init_module, "ComposeGenerator", FakeComposer)

    result = CliRunner().invoke(init_module.init_cmd, ["--profile", "observability"])

    assert result.exit_code == 0
    assert copied == ["postgres", "grafana"]
