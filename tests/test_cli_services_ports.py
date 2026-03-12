from __future__ import annotations

from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner

from phlo.cli.commands.services import ports as ports_module
from phlo.plugins.discovery import ServiceDefinition


def test_parse_compose_port_with_env_var() -> None:
    env_var, container_port = ports_module._parse_compose_port("${POSTGRES_PORT:-5432}:5432")
    assert env_var == "POSTGRES_PORT"
    assert container_port == "5432"


def test_parse_compose_port_with_default_only() -> None:
    env_var, container_port = ports_module._parse_compose_port("${POSTGRES_PORT}:5432")
    assert env_var == "POSTGRES_PORT"
    assert container_port == "5432"


def test_parse_compose_port_no_env() -> None:
    env_var, container_port = ports_module._parse_compose_port("5432:5432")
    assert env_var is None
    assert container_port == "5432"


def test_parse_compose_port_with_host_port() -> None:
    env_var, container_port = ports_module._parse_compose_port("10000:5432")
    assert env_var is None
    assert container_port == "5432"


def test_parse_compose_port_spec_with_host_port() -> None:
    spec = ports_module._parse_compose_port_spec("127.0.0.1:10000:5432")
    assert spec.env_var is None
    assert spec.host_port == "10000"
    assert spec.container_port == "5432"


def test_resolve_env_var_found() -> None:
    env = {"POSTGRES_PORT": "10000"}
    result = ports_module._resolve_env_var("POSTGRES_PORT", env)
    assert result == "10000"


def test_resolve_env_var_not_found() -> None:
    env: dict[str, str] = {}
    result = ports_module._resolve_env_var("POSTGRES_PORT", env)
    assert result is None


def test_resolve_env_var_none() -> None:
    env: dict[str, str] = {}
    result = ports_module._resolve_env_var(None, env)
    assert result is None


def test_detect_conflicts_no_conflicts() -> None:
    mappings = [
        ports_module.PortMapping(
            service="postgres",
            host_port=10000,
            container_port=5432,
            source="env",
            status="Running",
            env_var="POSTGRES_PORT",
        ),
        ports_module.PortMapping(
            service="minio",
            host_port=10001,
            container_port=9000,
            source="env",
            status="Running",
            env_var="MINIO_PORT",
        ),
    ]
    conflicts = ports_module._detect_conflicts(mappings)
    assert conflicts == []


def test_detect_conflicts_with_conflicts() -> None:
    mappings = [
        ports_module.PortMapping(
            service="postgres",
            host_port=10000,
            container_port=5432,
            source="env",
            status="Running",
            env_var="POSTGRES_PORT",
        ),
        ports_module.PortMapping(
            service="trino", host_port=8080, container_port=8080, source="default", status="Running"
        ),
        ports_module.PortMapping(
            service="hasura",
            host_port=8080,
            container_port=8080,
            source="default",
            status="Running",
        ),
    ]
    conflicts = ports_module._detect_conflicts(mappings)
    assert len(conflicts) == 1
    assert (conflicts[0][0], conflicts[0][1], conflicts[0][2]) == ("trino", "hasura", 8080)


def test_detect_conflicts_multiple_services_same_port() -> None:
    mappings = [
        ports_module.PortMapping(
            service="service1",
            host_port=8080,
            container_port=8080,
            source="default",
            status="Running",
        ),
        ports_module.PortMapping(
            service="service2",
            host_port=8080,
            container_port=8080,
            source="default",
            status="Running",
        ),
        ports_module.PortMapping(
            service="service3",
            host_port=8080,
            container_port=8080,
            source="default",
            status="Running",
        ),
    ]
    conflicts = ports_module._detect_conflicts(mappings)
    assert len(conflicts) >= 1


def test_ports_cmd_requires_phlo_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(ports_module.ports_cmd)
    assert result.exit_code == 1
    assert "Error: .phlo directory not found" in result.output


def test_ports_cmd_handles_no_services(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    (tmp_path / ".phlo").mkdir()
    (tmp_path / "phlo.yaml").write_text("name: test\n")

    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {}

    monkeypatch.setattr(ports_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(ports_module, "get_project_name", lambda: "test")
    monkeypatch.setattr(
        ports_module,
        "run_command",
        lambda *_args, **_kwargs: CompletedProcess(["docker", "ps"], 0, "", ""),
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(ports_module.ports_cmd)
    assert result.exit_code == 0
    assert "No port mappings found" in result.output


def test_ports_cmd_json_output(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    (tmp_path / ".phlo").mkdir()
    (tmp_path / "phlo.yaml").write_text("name: test\n")

    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {}

    monkeypatch.setattr(ports_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(ports_module, "get_project_name", lambda: "test")
    monkeypatch.setattr(
        ports_module,
        "run_command",
        lambda *_args, **_kwargs: CompletedProcess(["docker", "ps"], 0, "", ""),
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(ports_module.ports_cmd, ["--json"])
    assert result.exit_code == 0
    assert result.output.strip() == "[]"


def test_get_service_ports_with_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {"POSTGRES_PORT": "10000"}
    running_containers = {"postgres": {"status": "running", "ports": []}}
    show_all = False

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={"ports": ["${POSTGRES_PORT:-5432}:5432"]},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert len(ports) == 1
    assert ports[0].host_port == 10000
    assert ports[0].container_port == 5432
    assert ports[0].source == "env"
    assert ports[0].env_var == "POSTGRES_PORT"


def test_get_service_ports_with_default(monkeypatch: pytest.MonkeyPatch) -> None:
    env: dict[str, str] = {}
    running_containers: dict[str, dict] = {}
    show_all = True

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={"ports": ["${POSTGRES_PORT:-5432}:5432"]},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert len(ports) == 1
    assert ports[0].host_port == 5432
    assert ports[0].container_port == 5432
    assert ports[0].source == "default"


def test_get_service_ports_with_explicit_compose_host_port() -> None:
    env: dict[str, str] = {}
    running_containers: dict[str, dict] = {}
    show_all = True

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={"ports": ["15432:5432"]},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert len(ports) == 1
    assert ports[0].host_port == 15432
    assert ports[0].source == "compose"


def test_get_service_ports_prefers_runtime_mapping_over_default() -> None:
    env: dict[str, str] = {}
    running_containers = {
        "postgres": {
            "status": "running",
            "ports": [{"host_port": "15432", "container_port": "5432/tcp"}],
        }
    }
    show_all = False

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={"ports": ["${POSTGRES_PORT:-5432}:5432"]},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert len(ports) == 1
    assert ports[0].host_port == 15432
    assert ports[0].source == "runtime"


def test_load_environment_merges_config_and_shell_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    phlo_dir = tmp_path / ".phlo"
    phlo_dir.mkdir()
    (phlo_dir / ".env").write_text("POSTGRES_PORT=5432\nMINIO_PORT=9000\n")
    (phlo_dir / ".env.local").write_text("MINIO_PORT=9001\n")
    monkeypatch.setenv("POSTGRES_PORT", "15432")

    env = ports_module._load_environment(
        phlo_dir,
        {"env": {"POSTGRES_PORT": 15431, "TRINO_PORT": 18080}},
    )

    assert env["POSTGRES_PORT"] == "15432"
    assert env["MINIO_PORT"] == "9001"
    assert env["TRINO_PORT"] == "18080"


def test_get_service_ports_no_ports() -> None:
    env: dict[str, str] = {}
    running_containers: dict[str, dict] = {}
    show_all = False

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert ports == []


def test_get_service_ports_filters_stopped_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    env: dict[str, str] = {}
    running_containers: dict[str, dict] = {}
    show_all = False

    service = ServiceDefinition(
        name="postgres",
        description="PostgreSQL",
        compose={"ports": ["${POSTGRES_PORT:-5432}:5432"]},
    )

    ports = ports_module._get_service_ports(service, env, running_containers, show_all)
    assert ports == []


def test_ports_cmd_uses_phlo_yaml_env_and_service_port_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    (tmp_path / ".phlo").mkdir()
    (tmp_path / "phlo.yaml").write_text(
        """
name: test
env:
  POSTGRES_PORT: 15432
services:
  postgres:
    ports:
      - "16432:5432"
"""
    )

    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": ServiceDefinition(
                    name="postgres",
                    description="PostgreSQL",
                    compose={"ports": ["${POSTGRES_PORT:-5432}:5432"]},
                )
            }

    monkeypatch.setattr(ports_module, "ServiceDiscovery", FakeDiscovery)
    monkeypatch.setattr(ports_module, "get_project_name", lambda: "test")
    monkeypatch.setattr(ports_module, "_get_running_container_ports", lambda _project_name: {})
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(ports_module.ports_cmd, ["--all", "--json"])
    assert result.exit_code == 0
    assert result.output.strip() == (
        "[\n"
        "  {\n"
        '    "service": "postgres",\n'
        '    "host_port": 16432,\n'
        '    "container_port": 5432,\n'
        '    "source": "compose",\n'
        '    "status": "stopped",\n'
        '    "env_var": null\n'
        "  }\n"
        "]"
    )
