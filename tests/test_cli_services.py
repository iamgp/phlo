from __future__ import annotations

import os
from subprocess import CompletedProcess
from typing import cast

import pytest
import yaml
from click.testing import CliRunner
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
    """Build a service definition fixture.

    Args:
        name: Service name.
        default: Whether the service is enabled by default.
        profile: Optional profile name.
        category: Service category name.

    Returns:
        ServiceDefinition: Constructed service definition.
    """
    return ServiceDefinition(
        name=name,
        description=f"{name} service",
        category=category,
        default=default,
        profile=profile,
    )


def test_select_services_to_install_respects_enabled_disabled_and_profiles() -> None:
    """Verify service selection honors default, enabled, disabled, and profile behavior."""
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
    """Verify configured Dagster container name is selected when running.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Mock _resolve_container_name to return the configured name
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "myproj-dagster-webserver-1",
    )

    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: ["myproj-dagster-webserver-1"],
    )

    assert find_dagster_container("myproj") == "myproj-dagster-webserver-1"


def test_find_dagster_container_falls_back_to_new_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fallback to the new Dagster container name.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Mock _resolve_container_name to return something that won't match
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )

    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: ["myproj-dagster-1"],
    )

    assert find_dagster_container("myproj") == "myproj-dagster-1"


def test_get_profile_service_names_returns_profile_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify profile expansion returns all services in selected profiles.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    prometheus = _service("prometheus", profile="observability")
    grafana = _service("grafana", profile="observability")
    loki = _service("loki", profile="observability")
    hasura = _service("hasura", profile="api")
    postgres = _service("postgres", default=True)

    class FakeDiscovery:
        """Test double for service discovery profile lookups."""

        def get_services_by_profile(self, profile: str) -> list[ServiceDefinition]:
            """Return services matching the requested profile.

            Args:
                profile: Profile name to filter by.

            Returns:
                list[ServiceDefinition]: Matching services.
            """
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
    """Verify sibling phlo repository source path is detected.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.
    """
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
    """Verify PHLO_DEV_SOURCE accepts repository root path input.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.
    """
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
    """Verify compose generation injects development mounts for phlo.

    Args:
        tmp_path: Temporary directory fixture.
    """

    class FakeDiscovery:
        """Test double for compose dependency resolution."""

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            """Return service list unchanged.

            Args:
                services: Services to resolve.

            Returns:
                list[ServiceDefinition]: Input services unchanged.
            """
            return services

        def get_service(self, _name: str) -> None:
            """Return no service for lookup requests.

            Args:
                _name: Service name.

            Returns:
                None: Always none for this test double.
            """
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


def test_compose_generator_passthrough_compose_keys(tmp_path) -> None:
    """Verify compose keys pass through to generated service YAML.

    Args:
        tmp_path: Temporary directory fixture.
    """

    class FakeDiscovery:
        """Test double for compose dependency resolution."""

        def resolve_dependencies(
            self, services: list[ServiceDefinition]
        ) -> list[ServiceDefinition]:
            """Return service list unchanged.

            Args:
                services: Services to resolve.

            Returns:
                list[ServiceDefinition]: Input services unchanged.
            """
            return services

        def get_service(self, _name: str) -> None:
            """Return no service for lookup requests.

            Args:
                _name: Service name.

            Returns:
                None: Always none for this test double.
            """
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


def test_run_service_hooks_uses_sys_executable_when_project_venv_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Verify hook runner uses current interpreter when project venv is absent.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.
    """
    from phlo.cli.commands.services import utils as services_utils

    service = ServiceDefinition(
        name="dagster",
        description="Dagster",
        category="orchestration",
        hooks={"post_start": [{"command": ["python3", "-m", "phlo_dbt.hooks", "compile"]}]},
    )

    class FakeDiscovery:
        """Test double for service lookup."""

        def get_service(self, name: str):
            """Return service for matching name.

            Args:
                name: Service name.

            Returns:
                ServiceDefinition | None: Matching service or none.
            """
            return service if name == "dagster" else None

    calls: list[list[str]] = []

    def _fake_run_command(cmd, **_kwargs):
        """Capture command invocations and return successful process.

        Args:
            cmd: Command argument sequence.
            **_kwargs: Unused keyword arguments.

        Returns:
            CompletedProcess[str]: Successful command result.
        """
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
    """Verify hook runner prefers project venv python executable.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.
    """
    from phlo.cli.commands.services import utils as services_utils

    service = ServiceDefinition(
        name="dagster",
        description="Dagster",
        category="orchestration",
        hooks={"post_start": [{"command": ["python", "-m", "phlo_dbt.hooks", "compile"]}]},
    )

    class FakeDiscovery:
        """Test double for service lookup."""

        def get_service(self, name: str):
            """Return service for matching name.

            Args:
                name: Service name.

            Returns:
                ServiceDefinition | None: Matching service or none.
            """
            return service if name == "dagster" else None

    calls: list[list[str]] = []

    def _fake_run_command(cmd, **_kwargs):
        """Capture command invocations and return successful process.

        Args:
            cmd: Command argument sequence.
            **_kwargs: Unused keyword arguments.

        Returns:
            CompletedProcess[str]: Successful command result.
        """
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


def test_find_dagster_container_falls_back_to_legacy_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fallback to legacy Dagster container name.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )
    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: ["myproj-dagster-webserver-1"],
    )
    assert find_dagster_container("myproj") == "myproj-dagster-webserver-1"


def test_find_dagster_container_regex_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify regex-based fallback matches compatible container names.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )
    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: ["myproj-custom-dagster-web-1"],
    )
    assert find_dagster_container("myproj") == "myproj-custom-dagster-web-1"


def test_find_dagster_container_regex_excludes_daemon(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify regex fallback excludes daemon container names.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )
    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: ["myproj-dagster-daemon-1"],
    )
    with pytest.raises(RuntimeError, match="Could not find running Dagster"):
        find_dagster_container("myproj")


def test_find_dagster_container_raises_when_no_containers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify error is raised when no Dagster containers are running.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setattr(
        "phlo_dagster.containers._resolve_container_name",
        lambda service, project: "cfg",
    )
    monkeypatch.setattr(
        "phlo_dagster.containers._list_running_containers",
        lambda _project: [],
    )
    with pytest.raises(RuntimeError, match="Could not find running Dagster"):
        find_dagster_container("myproj")


def test_dagster_container_candidates_structure() -> None:
    """Verify candidate container names expose configured, new, and legacy values."""
    from phlo_dagster.containers import dagster_container_candidates

    candidates = dagster_container_candidates("demo", "demo-dagster-webserver-1")
    assert candidates.configured == "demo-dagster-webserver-1"
    assert candidates.new == "demo-dagster-1"
    assert candidates.legacy == "demo-dagster-webserver-1"


def test_dagster_container_candidates_no_configured() -> None:
    """Verify candidate names handle a missing configured container."""
    from phlo_dagster.containers import dagster_container_candidates

    candidates = dagster_container_candidates("demo", None)
    assert candidates.configured == ""
    assert candidates.new == "demo-dagster-1"


def test_select_first_existing_returns_first_match() -> None:
    """Verify first existing candidate is selected."""
    from phlo_dagster.containers import select_first_existing

    result = select_first_existing(
        ["a", "b", "c"],
        ["c", "b"],
    )
    assert result == "b"


def test_select_first_existing_returns_none_when_no_match() -> None:
    """Verify none is returned when no candidates match existing containers."""
    from phlo_dagster.containers import select_first_existing

    result = select_first_existing(["a", "b"], ["x", "y"])
    assert result is None


def test_select_first_existing_skips_empty_candidates() -> None:
    """Verify empty candidate names are ignored."""
    from phlo_dagster.containers import select_first_existing

    result = select_first_existing(["", "b"], ["b"])
    assert result == "b"


def test_extract_compose_service_from_label() -> None:
    """Verify compose service label parsing returns service name."""
    from phlo.cli.commands.services.list import _extract_compose_service

    info = {"Labels": "com.docker.compose.project=demo,com.docker.compose.service=postgres,other=x"}
    assert _extract_compose_service(info) == "postgres"


def test_extract_compose_service_returns_none_without_label() -> None:
    """Verify missing compose service labels return none."""
    from phlo.cli.commands.services.list import _extract_compose_service

    assert _extract_compose_service({"Labels": "some.other.label=val"}) is None
    assert _extract_compose_service({}) is None


def test_services_list_wraps_config_parse_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Verify invalid phlo.yaml config errors are reported as ClickException messages."""
    from phlo.cli.commands.services import list as list_module

    (tmp_path / "phlo.yaml").write_text("services: [\n")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(list_module.list_cmd, ["--json"])
    assert result.exit_code == 1
    assert "Failed to read" in result.output
    assert "Check YAML syntax and file permissions" in result.output


def test_services_list_wraps_discovery_failures(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Verify service discovery errors are reported as ClickException messages."""
    from phlo.cli.commands.services import list as list_module

    class FailingDiscovery:
        """Test double that raises during discovery."""

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
    """Verify services list command tolerates malformed docker JSON output.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.
    """
    from phlo.cli.commands.services import list as list_module

    class FakeDiscovery:
        """Test double returning an empty service map."""

        def discover(self) -> dict[str, ServiceDefinition]:
            """Return no services.

            Returns:
                dict[str, ServiceDefinition]: Empty service mapping.
            """
            return {}

    monkeypatch.setattr(list_module, "ServiceDiscovery", FakeDiscovery)
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


def test_resolve_dependencies_reports_cycle_path() -> None:
    """Verify dependency cycle errors include the cycle path."""
    discovery = ServiceDiscovery.__new__(ServiceDiscovery)
    discovery.services_dir = None
    discovery._services = {}
    discovery._loaded = True

    a = _service("a")
    a.depends_on = ["b"]
    b = _service("b")
    b.depends_on = ["c"]
    c = _service("c")
    c.depends_on = ["a"]

    with pytest.raises(ValueError, match="Circular dependency detected:.*→"):
        discovery.resolve_dependencies([a, b, c])


def test_resolve_dependencies_cycle_path_is_closed() -> None:
    """Verify reported cycle path is closed and formatted as expected."""
    discovery = ServiceDiscovery.__new__(ServiceDiscovery)
    discovery.services_dir = None
    discovery._services = {}
    discovery._loaded = True

    a = _service("a")
    a.depends_on = ["b"]
    b = _service("b")
    b.depends_on = ["a", "c"]
    c = _service("c")
    c.depends_on = ["b"]

    with pytest.raises(ValueError) as exc_info:
        discovery.resolve_dependencies([a, b, c])

    message = str(exc_info.value)
    assert "Circular dependency detected:" in message
    assert "→" in message
    assert "a → b → c" not in message


def test_find_cycles_returns_closed_paths() -> None:
    """Verify cycle finder returns closed cycle paths."""
    from phlo.plugins.discovery.services import _find_cycles

    graph = {
        "a": {"b"},
        "b": {"a", "c"},
        "c": {"b"},
    }
    cycles = _find_cycles({"a", "b", "c"}, graph)

    assert cycles
    assert all(len(cycle) > 2 and cycle[0] == cycle[-1] for cycle in cycles)


def test_resolve_dependencies_no_cycle() -> None:
    """Verify dependency resolution order is valid when graph is acyclic."""
    discovery = ServiceDiscovery.__new__(ServiceDiscovery)
    discovery.services_dir = None
    discovery._services = {}
    discovery._loaded = True

    a = _service("a")
    b = _service("b")
    b.depends_on = ["a"]
    c = _service("c")
    c.depends_on = ["b"]

    result = discovery.resolve_dependencies([a, b, c])
    names = [s.name for s in result]
    assert names.index("a") < names.index("b") < names.index("c")


def test_services_init_excludes_profile_services_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Verify init only includes default services unless profile is requested."""

    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": _service("postgres", default=True),
                "prometheus": _service("prometheus", profile="observability"),
            }

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
    """Verify init includes profile services when --profile is passed."""

    class FakeDiscovery:
        def discover(self) -> dict[str, ServiceDefinition]:
            return {
                "postgres": _service("postgres", default=True),
                "prometheus": _service("prometheus", profile="observability"),
            }

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
