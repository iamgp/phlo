"""Reusable profile-level test harnesses for real Phlo service stacks.

Provides infrastructure for integration testing against live Phlo service
stacks, including bundled stack setup, service lifecycle management, and
verification helpers.

This module enables contract tests that validate the full stack works
correctly with real services (Postgres, MinIO, Nessie, Trino, Dagster, etc.).

Example:
    >>> from phlo_testing import bootstrap_bundled_stack_harness
    >>> harness = bootstrap_bundled_stack_harness()
    >>> harness.materialize("posts", partition_date="2024-01-01")
    >>> harness.cleanup()

Key Components:
    - BundledStackHarness: Runtime handle for managing a full Phlo stack
    - BundledStackPorts: Service port configuration
    - bootstrap_bundled_stack_harness(): Factory function to create harnesses
    - Service verification methods for API, observability, and lineage stacks

"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import urllib.parse
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import psycopg2
import requests
from dagster import DagsterRunStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster_graphql.client.client import DagsterGraphQLClient

BUNDLED_STACK_CORE_SERVICES = (
    "postgres",
    "minio",
    "minio-setup",
    "nessie",
    "trino",
    "dagster",
    "dagster-daemon",
)
# Core services required for the bundled stack.

BUNDLED_STACK_DEV_PACKAGES = (
    "phlo-alerting",
    "phlo-alloy",
    "phlo-dagster",
    "phlo-dlt",
    "phlo-dbt",
    "phlo-grafana",
    "phlo-iceberg",
    "phlo-hasura",
    "phlo-lineage",
    "phlo-loki",
    "phlo-minio",
    "phlo-nessie",
    "phlo-observatory",
    "phlo-openmetadata",
    "phlo-pgweb",
    "phlo-postgres",
    "phlo-postgrest",
    "phlo-prometheus",
    "phlo-superset",
    "phlo-trino",
    "phlo-api",
)
# Development packages included in the bundled stack.

BUNDLED_STACK_OPTIONAL_PACKAGES = (
    "phlo-alerting",
    "phlo-alloy",
    "phlo-grafana",
    "phlo-lineage",
    "phlo-loki",
    "phlo-openmetadata",
    "phlo-pgweb",
    "phlo-prometheus",
)
# Optional packages that can be added to the bundled stack.

BUNDLED_STACK_OPTIONAL_SERVICE_PLUGINS = (
    "phlo-alloy",
    "phlo-grafana",
    "phlo-loki",
    "phlo-openmetadata",
    "phlo-pgweb",
    "phlo-prometheus",
)
# Optional service plugins for the bundled stack.

_BUNDLED_STACK_PORT_DEFAULTS = {
    "PHLO_API_PORT": ("Phlo API", 54000),
    "DAGSTER_PORT": ("Dagster", 3000),
    "OBSERVATORY_PORT": ("Observatory", 3001),
    "HASURA_PORT": ("Hasura", 8082),
    "POSTGREST_PORT": ("PostgREST", 3002),
    "PGWEB_PORT": ("pgweb", 8081),
    "POSTGRES_PORT": ("Postgres", 5432),
    "TRINO_PORT": ("Trino", 8080),
    "MINIO_API_PORT": ("MinIO API", 9000),
    "MINIO_CONSOLE_PORT": ("MinIO Console", 9001),
    "NESSIE_PORT": ("Nessie", 19120),
    "PROMETHEUS_PORT": ("Prometheus", 9090),
    "LOKI_PORT": ("Loki", 3100),
    "GRAFANA_PORT": ("Grafana", 3003),
    "ALLOY_PORT": ("Alloy", 12345),
    "SUPERSET_PORT": ("Superset", 8088),
    "OPENMETADATA_PORT": ("OpenMetadata", 8585),
}
# Default port mappings for bundled stack services.

_GOLDEN_PATH_MODULE: Any | None = None


def _repo_root() -> Path:
    """Return the repository root directory.

    Returns:
        Path to the repository root.

    """
    return Path(__file__).resolve().parents[4]


def _load_golden_path_module() -> Any:
    """Load the golden path module from scripts directory.

    Returns:
        The loaded golden path module.

    Raises:
        RuntimeError: If the module cannot be loaded.

    """
    global _GOLDEN_PATH_MODULE
    if _GOLDEN_PATH_MODULE is not None:
        return _GOLDEN_PATH_MODULE

    module_path = _repo_root() / "scripts" / "run_golden_path.py"
    spec = importlib.util.spec_from_file_location("phlo_testing_run_golden_path", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load golden-path utilities from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _GOLDEN_PATH_MODULE = module
    return module


def _repo_python_executable() -> Path:
    """Return the Python executable for the repository.

    Returns:
        Path to the Python executable, preferring the repo's .venv.

    """
    repo_python = _repo_root() / ".venv" / "bin" / "python"
    if repo_python.exists():
        return repo_python
    return Path(sys.executable)


def _repo_pythonpath() -> str:
    """Build PYTHONPATH for repository execution.

    Returns:
        PYTHONPATH string including repo src and packages.

    """
    repo_root = _repo_root()
    entries = [repo_root / "src", *(repo_root / "packages").glob("*/src")]
    rendered = os.pathsep.join(str(path) for path in entries)
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        return f"{rendered}{os.pathsep}{existing}"
    return rendered


def _run_repo_phlo(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None,
    stream_output: bool,
) -> subprocess.CompletedProcess[str]:
    """Execute phlo CLI command in the repository context.

    Args:
        args: Command line arguments for phlo CLI.
        cwd: Working directory for command execution.
        timeout: Maximum time to wait for command completion (seconds).
        stream_output: If True, stream output in real-time; otherwise capture.

    Returns:
        CompletedProcess with command results.

    Raises:
        RuntimeError: If the command fails (non-zero exit code).

    """
    command = [str(_repo_python_executable()), "-m", "phlo.cli.main", *args]
    env = {**os.environ, "PYTHONPATH": _repo_pythonpath()}

    if stream_output:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines: list[str] = []
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    print(f"    {line}", end="")
                    output_lines.append(line)
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            raise
        result = subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout="".join(output_lines),
            stderr="",
        )
    else:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")
    return result


def bundled_stack_contract_enabled() -> bool:
    """Check if bundled stack contract tests are enabled.

    Returns:
        True if PHLO_RUN_BUNDLED_STACK_CONTRACT is set to a truthy value.

    """
    value = os.environ.get("PHLO_RUN_BUNDLED_STACK_CONTRACT", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def keep_bundled_stack_running() -> bool:
    """Check if bundled stack should be kept running after tests.

    Returns:
        True if PHLO_KEEP_BUNDLED_STACK is set to a truthy value.

    """
    value = os.environ.get("PHLO_KEEP_BUNDLED_STACK", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def default_bundled_stack_project_dir(base_dir: Path | None = None) -> Path:
    """Generate a default project directory path for bundled stack tests.

    Args:
        base_dir: Base directory for project creation. Defaults to .tmp in repo root.

    Returns:
        Path to a unique project directory with UUID suffix.

    """
    root = base_dir or (_repo_root() / ".tmp")
    return root / f"phlo-bundled-stack-{uuid.uuid4().hex[:8]}"


def _cleanup_existing_bundled_stack_projects(base_dir: Path, *, stream_output: bool) -> None:
    """Clean up existing bundled stack projects and Docker resources.

    Stops services and removes containers/networks from previous test runs.

    Args:
        base_dir: Directory containing bundled stack projects.
        stream_output: Whether to stream command output.

    """
    utils = _load_golden_path_module()
    for project_dir in sorted(base_dir.glob("phlo-bundled-stack-*")):
        phlo_dir = project_dir / ".phlo"
        python_executable = project_dir / ".venv" / "bin" / "python"

        if phlo_dir.exists() and python_executable.exists():
            with contextlib.suppress(Exception):
                utils.run_phlo(
                    ["services", "stop", "--native"],
                    cwd=project_dir,
                    timeout=120,
                    check=False,
                    stream_output=stream_output,
                    python_exe=python_executable,
                )
            with contextlib.suppress(Exception):
                utils.run_phlo(
                    ["services", "stop"],
                    cwd=project_dir,
                    timeout=180,
                    check=False,
                    stream_output=stream_output,
                    python_exe=python_executable,
                )

        with contextlib.suppress(Exception):
            utils.force_remove_directory(project_dir)

    with contextlib.suppress(Exception):
        container_result = subprocess.run(
            ["docker", "ps", "-aq", "--filter", "name=phlo-bundled-stack-"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        container_ids = [
            line.strip() for line in container_result.stdout.splitlines() if line.strip()
        ]
        if container_ids:
            subprocess.run(
                ["docker", "rm", "-f", *container_ids],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )

    with contextlib.suppress(Exception):
        network_result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        network_names = [
            line.strip()
            for line in network_result.stdout.splitlines()
            if line.strip().startswith("phlo-bundled-stack-")
        ]
        if network_names:
            subprocess.run(
                ["docker", "network", "rm", *network_names],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )


def _port_in_use(port: int) -> bool:
    """Check if a TCP port is in use.

    Args:
        port: Port number to check.

    Returns:
        True if the port is already in use.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _allocate_unique_port(
    service_name: str,
    default_port: int,
    *,
    resolve_port: Any,
    used_ports: set[int],
) -> int:
    """Allocate a unique port for a service, avoiding conflicts.

    Args:
        service_name: Name of the service.
        default_port: Default port to start from.
        resolve_port: Function to resolve port (may increment).
        used_ports: Set of already allocated ports.

    Returns:
        An available port number.

    """
    candidate = int(resolve_port(service_name, default_port))
    while candidate in used_ports or _port_in_use(candidate):
        candidate += 1
    used_ports.add(candidate)
    return candidate


def build_bundled_stack_env_updates(
    resolve_port: Any, *, project_name: str | None = None
) -> dict[str, str]:
    """Build environment variable updates for bundled stack ports.

    Args:
        resolve_port: Function to resolve service ports.
        project_name: Stable project identity for generated service processes.

    Returns:
        Dictionary of environment variable updates with unique ports.

    """
    used_ports: set[int] = set()
    updates = {
        env_key: str(
            _allocate_unique_port(
                service_name,
                default_port,
                resolve_port=resolve_port,
                used_ports=used_ports,
            )
        )
        for env_key, (service_name, default_port) in _BUNDLED_STACK_PORT_DEFAULTS.items()
    }
    updates["PHLO_DEV_EXTRA_PACKAGES"] = ",".join(BUNDLED_STACK_DEV_PACKAGES)
    if project_name:
        updates["PHLO_PROJECT"] = project_name
    updates["PHLO_WAP_SENSORS_ENABLED"] = "true"
    updates["PHLO_WAP_BRANCH_CREATION_INTERVAL_SECONDS"] = "1"
    updates["PHLO_WAP_PROMOTION_INTERVAL_SECONDS"] = "1"
    return updates


def _verify_bind_mount_parent(path: Path, *, attempts: int = 5, delay_seconds: float = 0.5) -> None:
    """Verify Docker can read a marker file from the target parent path.

    Args:
        path: Directory path to verify.
        attempts: Number of retry attempts.
        delay_seconds: Delay between attempts.

    Raises:
        RuntimeError: If Docker cannot bind-mount the directory.

    """
    target_path = path.resolve()
    target_path.mkdir(parents=True, exist_ok=True)
    marker = f".phlo_bind_check_{uuid.uuid4().hex}"
    marker_path = target_path / marker
    marker_path.write_text("ok\n")
    try:
        last_detail = "unknown bind mount error"
        for _ in range(attempts):
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{target_path}:/mnt:ro",
                    "alpine:3.20",
                    "sh",
                    "-lc",
                    f"test -f /mnt/{marker}",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            if result.returncode == 0:
                return
            last_detail = (
                result.stderr.strip() or result.stdout.strip() or "unknown bind mount error"
            )
            time.sleep(delay_seconds)
        raise RuntimeError(
            "Docker cannot bind-mount the contract test project directory: "
            f"{target_path} ({last_detail})"
        )
    finally:
        marker_path.unlink(missing_ok=True)


@dataclass(slots=True)
class BundledStackPorts:
    """Resolved host ports for the bundled-stack contract harness.

    Attributes:
        phlo_api: Port for Phlo API service.
        dagster: Port for Dagster webserver.
        observatory: Port for Observatory UI (default: 3001).
        hasura: Port for Hasura GraphQL (default: 8082).
        postgrest: Port for PostgREST API (default: 3002).
        pgweb: Port for pgweb UI (default: 8081).
        postgres: Port for PostgreSQL (default: 5432).
        trino: Port for Trino (default: 8080).
        minio_api: Port for MinIO API (default: 9000).
        minio_console: Port for MinIO Console (default: 9001).
        nessie: Port for Nessie catalog (default: 19120).
        prometheus: Port for Prometheus (default: 9090).
        loki: Port for Loki logging (default: 3100).
        grafana: Port for Grafana (default: 3003).
        alloy: Port for Alloy (default: 12345).
        superset: Port for Superset (default: 8088).
        openmetadata: Port for OpenMetadata (default: 8585).

    """

    phlo_api: int
    dagster: int
    observatory: int = 3001
    hasura: int = 8082
    postgrest: int = 3002
    pgweb: int = 8081
    postgres: int = 5432
    trino: int = 8080
    minio_api: int = 9000
    minio_console: int = 9001
    nessie: int = 19120
    prometheus: int = 9090
    loki: int = 3100
    grafana: int = 3003
    alloy: int = 12345
    superset: int = 8088
    openmetadata: int = 8585

    @classmethod
    def from_env(cls, env_vars: dict[str, str]) -> BundledStackPorts:
        """Create BundledStackPorts from environment variables.

        Args:
            env_vars: Dictionary of environment variables.

        Returns:
            BundledStackPorts instance with ports from environment.

        """
        return cls(
            phlo_api=int(env_vars.get("PHLO_API_PORT", "54000")),
            dagster=int(env_vars.get("DAGSTER_PORT", "3000")),
            observatory=int(env_vars.get("OBSERVATORY_PORT", "3001")),
            hasura=int(env_vars.get("HASURA_PORT", "8082")),
            postgrest=int(env_vars.get("POSTGREST_PORT", "3002")),
            pgweb=int(env_vars.get("PGWEB_PORT", "8081")),
            postgres=int(env_vars.get("POSTGRES_PORT", "5432")),
            trino=int(env_vars.get("TRINO_PORT", "8080")),
            minio_api=int(env_vars.get("MINIO_API_PORT", "9000")),
            minio_console=int(env_vars.get("MINIO_CONSOLE_PORT", "9001")),
            nessie=int(env_vars.get("NESSIE_PORT", "19120")),
            prometheus=int(env_vars.get("PROMETHEUS_PORT", "9090")),
            loki=int(env_vars.get("LOKI_PORT", "3100")),
            grafana=int(env_vars.get("GRAFANA_PORT", "3003")),
            alloy=int(env_vars.get("ALLOY_PORT", "12345")),
            superset=int(env_vars.get("SUPERSET_PORT", "8088")),
            openmetadata=int(env_vars.get("OPENMETADATA_PORT", "8585")),
        )


@dataclass(slots=True)
class BundledStackHarness:
    """Runtime handle for a real bundled-stack contract environment.

    Manages a full Phlo service stack for integration testing, providing
    methods to start/stop services, run materializations, and verify
    the health of various stack components.

    Attributes:
        project_dir: Path to the temporary project directory.
        phlo_source: Path to the Phlo source repository.
        python_executable: Path to the Python executable for the project.
        ports: BundledStackPorts with resolved service ports.
        keep_running: If True, keep services running after tests.

    Example:
        >>> harness = bootstrap_bundled_stack_harness()
        >>> harness.materialize("posts", partition_date="2024-01-01")
        >>> harness.verify_api_stack()
        >>> harness.cleanup()

    """

    project_dir: Path
    phlo_source: Path
    python_executable: Path
    ports: BundledStackPorts
    keep_running: bool = False

    def dagster_graphql_client(self) -> DagsterGraphQLClient:
        """Return a Dagster GraphQL client for the live harness.

        Returns:
            DagsterGraphQLClient configured for the harness's Dagster instance.

        """
        return DagsterGraphQLClient("127.0.0.1", port_number=self.ports.dagster)

    def run_phlo(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
        check: bool = True,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a phlo CLI command in the harness project.

        Args:
            args: Command line arguments for phlo CLI.
            timeout: Maximum time to wait for command completion (seconds).
            check: If True, raise RuntimeError on non-zero exit code.
            stream_output: If True, stream output in real-time.

        Returns:
            CompletedProcess with command results.

        Raises:
            RuntimeError: If the command fails and check=True.

        """
        utils = _load_golden_path_module()
        return utils.run_phlo(
            args,
            cwd=self.project_dir,
            timeout=timeout,
            check=check,
            stream_output=stream_output,
            python_exe=self.python_executable,
        )

    def read_env(self) -> dict[str, str]:
        """Read resolved environment variables from the project's .phlo files.

        Returns:
            Dictionary of environment variables with .env.local overriding .env.

        """
        utils = _load_golden_path_module()
        phlo_dir = self.project_dir / ".phlo"
        env_vars = cast(dict[str, str], utils.read_env_file(phlo_dir / ".env"))
        local_env_path = phlo_dir / ".env.local"
        if local_env_path.exists():
            env_vars.update(cast(dict[str, str], utils.read_env_file(local_env_path)))
        return env_vars

    def default_partition_date(self) -> str:
        """Return a default partition date (yesterday).

        Returns:
            ISO format date string for yesterday.

        """
        return (datetime.now(UTC).date() - timedelta(days=1)).isoformat()

    def _utils(self) -> Any:
        """Load and return the golden path utilities module.

        Returns:
            The golden path module with utility functions.

        """
        return _load_golden_path_module()

    @contextlib.contextmanager
    def _temporary_env(self, updates: Mapping[str, str | None]) -> Any:
        """Temporarily update environment variables.

        Args:
            updates: Dictionary of environment variable updates.
                Values of None will delete the variable.

        Yields:
            None

        Example:
            >>> with self._temporary_env({"KEY": "value"}):
            ...     # Environment updated
            ...     pass
            >>> # Environment restored

        """
        previous = {key: os.environ.get(key) for key in updates}
        try:
            for key, value in updates.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def install_workspace_packages(
        self,
        package_names: tuple[str, ...] | list[str],
        *,
        timeout: int = 600,
    ) -> None:
        """Install workspace packages into the harness environment.

        Args:
            package_names: Names of packages to install from the workspace.
            timeout: Maximum time for installation (seconds).

        Raises:
            RuntimeError: If a package is not found in the workspace.

        """
        if not package_names:
            return

        install_args = ["uv", "pip", "install", "--python", str(self.python_executable)]
        for package_name in package_names:
            package_path = self.phlo_source / "packages" / package_name
            if not package_path.exists():
                raise RuntimeError(f"Workspace package not found: {package_name}")
            install_args.extend(["-e", str(package_path)])
        self._utils().run_command(install_args, cwd=self.project_dir, timeout=timeout)

    def ensure_full_stack_packages(self) -> None:
        """Install all optional packages for full stack testing."""
        self.install_workspace_packages(BUNDLED_STACK_OPTIONAL_PACKAGES)

    def add_services(
        self, service_names: tuple[str, ...] | list[str], *, timeout: int = 180
    ) -> None:
        """Add services to the project without starting them.

        Args:
            service_names: Names of services to add.
            timeout: Maximum time for operation (seconds).

        """
        for service_name in service_names:
            self.run_phlo(
                ["services", "add", service_name, "--no-start"],
                timeout=timeout,
                stream_output=True,
            )

    def start_services(
        self,
        service_names: tuple[str, ...] | list[str],
        *,
        timeout: int = 600,
        native: bool = False,
    ) -> None:
        """Start specified services.

        Args:
            service_names: Names of services to start.
            timeout: Maximum time for startup (seconds).
            native: If True, start native services only (no Docker).

        """
        if not service_names:
            return
        args = ["services", "start"]
        if native:
            args.append("--native")
        for service_name in service_names:
            args.extend(["--service", service_name])
        self.run_phlo(args, timeout=timeout, stream_output=True)

    def wait_for_http(self, url: str, *, name: str, timeout: int = 120) -> None:
        """Wait for an HTTP endpoint to become available.

        Args:
            url: URL to poll.
            name: Service name for error messages.
            timeout: Maximum time to wait (seconds).

        Raises:
            RuntimeError: If the endpoint doesn't become ready in time.

        """
        if not self._utils().wait_for_http(url, name=name, timeout=timeout):
            raise RuntimeError(f"{name} did not become ready: {url}")

    def http_get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any] | list[Any] | str:
        """Make an HTTP GET request.

        Args:
            url: URL to request.
            headers: Optional request headers.
            timeout: Request timeout (seconds).

        Returns:
            Parsed JSON response or raw string.

        """
        return cast(
            dict[str, Any] | list[Any] | str,
            self._utils().http_get(url, headers=headers, timeout=timeout),
        )

    def http_post(
        self,
        url: str,
        data: dict[str, Any] | str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> dict[str, Any] | list[Any] | str:
        """Make an HTTP POST request.

        Args:
            url: URL to request.
            data: Request body (JSON dict or string).
            headers: Optional request headers.
            timeout: Request timeout (seconds).

        Returns:
            Parsed JSON response or raw string.

        """
        return cast(
            dict[str, Any] | list[Any] | str,
            self._utils().http_post(url, data, headers=headers, timeout=timeout),
        )

    def run_python(
        self,
        code: str,
        *,
        env_updates: dict[str, str] | None = None,
        timeout: int = 60,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute Python code in the harness environment.

        Args:
            code: Python code to execute.
            env_updates: Environment variable updates for execution.
            timeout: Maximum execution time (seconds).
            check: If True, raise on non-zero exit code.

        Returns:
            CompletedProcess with execution results.

        """
        env = os.environ.copy()
        if env_updates:
            env.update(env_updates)
        return subprocess.run(
            [str(self.python_executable), "-c", code],
            cwd=self.project_dir,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=check,
        )

    def run_command(
        self,
        args: list[str],
        *,
        timeout: int = 60,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a shell command in the project directory.

        Args:
            args: Command arguments.
            timeout: Maximum execution time (seconds).
            check: If True, raise on non-zero exit code.

        Returns:
            CompletedProcess with execution results.

        """
        return subprocess.run(
            args,
            cwd=self.project_dir,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=check,
        )

    def host_lineage_db_url(self) -> str:
        """Build a PostgreSQL connection URL for the lineage database.

        Returns:
            PostgreSQL connection string for host access.

        """
        env_vars = self.read_env()
        return (
            "postgresql://"
            f"{env_vars.get('POSTGRES_USER', 'phlo')}:"
            f"{env_vars.get('POSTGRES_PASSWORD', 'phlo')}"
            f"@localhost:{self.ports.postgres}/{env_vars.get('POSTGRES_DB', 'phlo')}"
        )

    def verify_default_frontends(self) -> None:
        """Verify Phlo API and Observatory are accessible.

        Starts the services and performs health checks.

        Raises:
            RuntimeError: If services fail to start or respond.
            AssertionError: If health checks fail.

        """
        self.start_services(["phlo-api", "observatory"], timeout=600, native=True)
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.phlo_api}/health",
            name="Phlo API",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.observatory}/",
            name="Observatory",
            timeout=180,
        )
        observatory_response = requests.get(
            f"http://127.0.0.1:{self.ports.observatory}/",
            timeout=30,
        )
        observatory_response.raise_for_status()
        assert "text/html" in observatory_response.headers.get("content-type", "")

    def verify_api_stack(self) -> None:
        """Verify the API stack (Hasura, PostgREST, pgweb) is functional.

        Adds services if needed, starts them, and performs health checks
        and basic functionality tests.

        Raises:
            RuntimeError: If services fail to start.
            AssertionError: If health checks or API tests fail.

        """
        self.add_services(["hasura", "postgrest", "pgweb"])
        self.start_services(["hasura", "postgrest", "pgweb"], timeout=600)

        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.hasura}/healthz",
            name="Hasura",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.postgrest}/",
            name="PostgREST",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.pgweb}/",
            name="pgweb",
            timeout=120,
        )

        env_vars = self.read_env()
        hasura_secret = env_vars.get("HASURA_ADMIN_SECRET", "phlo-hasura-admin-secret")
        graphql_result = self.http_post(
            f"http://127.0.0.1:{self.ports.hasura}/v1/graphql",
            {
                "query": """
                    query {
                        marts_posts_mart(limit: 5) {
                            id
                            title
                        }
                    }
                """
            },
            headers={"x-hasura-admin-secret": hasura_secret},
        )
        assert isinstance(graphql_result, dict)
        rows = graphql_result.get("data", {}).get("marts_posts_mart")
        assert isinstance(rows, list)
        assert rows

        rest_result = self.http_get(
            f"http://127.0.0.1:{self.ports.postgrest}/posts_mart?limit=5",
            headers={"Accept": "application/json"},
        )
        assert isinstance(rest_result, list)
        assert rest_result

        pgweb_response = requests.get(f"http://127.0.0.1:{self.ports.pgweb}/", timeout=30)
        pgweb_response.raise_for_status()
        assert "pgweb" in pgweb_response.text.lower()

        backends = self.http_get(f"http://127.0.0.1:{self.ports.phlo_api}/api/backends")
        assert isinstance(backends, list)
        assert any(
            isinstance(backend, dict)
            and backend.get("name") == "hasura"
            and backend.get("healthy") is True
            for backend in backends
        )

    def verify_observability_stack(self) -> None:
        """Verify the observability stack (Prometheus, Loki, Alloy, Grafana).

        Adds services if needed, starts them, and performs health checks
        and basic functionality tests.

        Raises:
            RuntimeError: If services fail to start.
            AssertionError: If health checks or API tests fail.

        """
        self.add_services(["prometheus", "loki", "alloy", "grafana"])
        self.start_services(["prometheus", "loki", "alloy", "grafana"], timeout=900)

        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.prometheus}/-/healthy",
            name="Prometheus",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.loki}/ready",
            name="Loki",
            timeout=180,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.alloy}/-/ready",
            name="Alloy",
            timeout=120,
        )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.grafana}/api/health",
            name="Grafana",
            timeout=180,
        )

        prometheus_targets = self.http_get(
            f"http://127.0.0.1:{self.ports.prometheus}/api/v1/targets"
        )
        assert isinstance(prometheus_targets, dict)
        active_targets = prometheus_targets.get("data", {}).get("activeTargets")
        assert isinstance(active_targets, list)
        assert any(
            target.get("health") == "up" for target in active_targets if isinstance(target, dict)
        )

        loki_labels = self.http_get(f"http://127.0.0.1:{self.ports.loki}/loki/api/v1/labels")
        assert isinstance(loki_labels, dict)
        assert isinstance(loki_labels.get("data"), list)

        grafana_datasources = self.http_get(
            f"http://127.0.0.1:{self.ports.grafana}/api/datasources",
            headers={"Authorization": "Basic YWRtaW46YWRtaW4="},
        )
        assert isinstance(grafana_datasources, list)
        assert grafana_datasources

    def verify_superset(self) -> None:
        """Verify Apache Superset is functional.

        Adds the service if needed, starts it, and performs health checks.

        Raises:
            RuntimeError: If service fails to start.
            AssertionError: If health check fails.

        """
        self.add_services(["superset"])
        self.start_services(["superset"], timeout=900)
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.superset}/health",
            name="Superset",
            timeout=300,
        )
        health = self.http_get(f"http://127.0.0.1:{self.ports.superset}/health")
        if isinstance(health, dict):
            assert health.get("status") == "OK"
            return
        assert isinstance(health, str)
        assert health.strip().upper() == "OK"

    def verify_metrics_cli(self) -> None:
        """Verify the metrics CLI command works.

        Runs 'phlo metrics summary' and checks output.

        Raises:
            AssertionError: If command output doesn't contain expected content.

        """
        result = self.run_phlo(
            ["metrics", "summary", "--period", "24h"],
            timeout=120,
            stream_output=False,
        )
        assert "Platform Metrics Summary" in result.stdout

    def verify_alerting_cli(self) -> None:
        """Verify the alerting CLI command works.

        Runs 'phlo alerts list' with a mock webhook and checks output.

        Raises:
            AssertionError: If command output doesn't contain expected content.

        """
        env_updates = {"PHLO_ALERT_SLACK_WEBHOOK": "https://example.com/mock"}
        with self._temporary_env(env_updates):
            result = self.run_phlo(
                ["alerts", "list"],
                timeout=120,
                stream_output=False,
            )
        assert "slack" in result.stdout.lower()

    def emit_lineage_smoke_events(
        self,
        *,
        source_asset: str,
        target_asset: str,
        metadata: dict[str, Any] | None = None,
        env_updates: dict[str, str] | None = None,
    ) -> None:
        """Emit lineage events for smoke testing.

        Args:
            source_asset: Source asset key (e.g., "raw.posts").
            target_asset: Target asset key (e.g., "raw_marts.posts_mart").
            metadata: Optional metadata to include with the event.
            env_updates: Optional environment variable updates.

        """
        metadata_json = json.dumps(metadata or {"source": "bundled_stack_contract"})
        code = f"""
from phlo.hooks.emitters import LineageEventContext, LineageEventEmitter

LineageEventEmitter(LineageEventContext(tags={{"source": "bundled_stack_contract"}})).emit_edges(
    edges=[({source_asset!r}, {target_asset!r})],
    asset_keys=[{target_asset!r}],
    metadata={metadata_json},
)
"""
        self.run_python(code, env_updates=env_updates, timeout=60)

    def verify_lineage_cli(self) -> None:
        """Verify the lineage CLI command works.

        Emits smoke events, exports lineage, and verifies the export contains
        expected assets and edges.

        Raises:
            AssertionError: If export doesn't contain expected content.

        """
        lineage_db_url = self.host_lineage_db_url()
        self.emit_lineage_smoke_events(
            source_asset="raw.posts",
            target_asset="raw_marts.posts_mart",
            env_updates={"LINEAGE_DB_URL": lineage_db_url},
        )

        export_path = self.project_dir / ".phlo" / "lineage_contract_export.json"
        with self._temporary_env({"LINEAGE_DB_URL": lineage_db_url}):
            self.run_phlo(
                [
                    "lineage",
                    "export",
                    "raw_marts.posts_mart",
                    "--format",
                    "json",
                    "--output",
                    str(export_path),
                ],
                timeout=120,
                stream_output=False,
            )
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        assert "raw.posts" in payload.get("assets", {})
        assert "raw_marts.posts_mart" in payload.get("assets", {})
        assert "raw_marts.posts_mart" in payload.get("edges", {}).get("raw.posts", [])

    def verify_openmetadata(self) -> None:
        """Verify OpenMetadata integration works.

        Starts OpenMetadata, syncs metadata, emits events, and verifies
        the lineage and quality data appears in OpenMetadata.

        Raises:
            RuntimeError: If service fails to start or sync fails.
            AssertionError: If metadata or lineage checks fail.

        """
        self.add_services(["openmetadata"])
        result = self.run_phlo(
            ["services", "start", "--service", "openmetadata"],
            timeout=1500,
            stream_output=True,
            check=False,
        )
        if result.returncode != 0:
            project_name = self.project_dir.name
            setup_container = f"{project_name}-openmetadata-setup-1"
            server_container = f"{project_name}-openmetadata-1"
            setup_result = self.run_command(
                ["docker", "start", "-a", setup_container],
                timeout=1500,
                check=False,
            )
            if setup_result.returncode != 0:
                raise RuntimeError(
                    setup_result.stdout or setup_result.stderr or "openmetadata setup failed"
                )
            server_result = self.run_command(
                ["docker", "start", server_container],
                timeout=60,
                check=False,
            )
            if server_result.returncode != 0:
                raise RuntimeError(
                    server_result.stdout
                    or server_result.stderr
                    or "openmetadata server failed to start"
                )
        self.wait_for_http(
            f"http://127.0.0.1:{self.ports.openmetadata}/api/v1/system/version",
            name="OpenMetadata",
            timeout=900,
        )

        env_vars = self.read_env()
        om_service = env_vars.get("OPENMETADATA_SERVICE_NAME", "phlo")
        om_database = env_vars.get(
            "OPENMETADATA_DATABASE_NAME",
            env_vars.get("TRINO_CATALOG", "iceberg"),
        )
        sync_env = {
            "OPENMETADATA_HOST": "127.0.0.1",
            "OPENMETADATA_PORT": str(self.ports.openmetadata),
            "OPENMETADATA_SERVICE_NAME": om_service,
            "OPENMETADATA_SERVICE_TYPE": env_vars.get("OPENMETADATA_SERVICE_TYPE", "Trino"),
            "OPENMETADATA_DATABASE_NAME": om_database,
            "NESSIE_HOST": "127.0.0.1",
            "NESSIE_PORT": str(self.ports.nessie),
            "TRINO_HOST": "127.0.0.1",
            "TRINO_PORT": str(self.ports.trino),
        }
        with self._temporary_env(sync_env):
            self.run_phlo(["openmetadata", "sync"], timeout=900, stream_output=False)

        om_user = env_vars.get("OPENMETADATA_USERNAME", "admin")
        om_pass = env_vars.get("OPENMETADATA_PASSWORD", "admin")
        om_base_url = f"http://127.0.0.1:{self.ports.openmetadata}"
        om_token = self._utils().openmetadata_login(
            om_base_url,
            username=om_user,
            password=om_pass,
        )
        table_fqn = f"{om_service}.{om_database}.raw_marts.posts_mart"
        source_fqn = f"{om_service}.{om_database}.raw.posts"
        table = self._utils().openmetadata_get_with_fallback(
            [f"{om_base_url}/api/v1/tables/name/{urllib.parse.quote(table_fqn, safe='')}"],
            token=om_token,
            username=om_user,
            password=om_pass,
            timeout=30,
        )
        assert isinstance(table, dict)
        assert table.get("name") == "posts_mart"

        emit_env = {
            **sync_env,
            "OPENMETADATA_USERNAME": om_user,
            "OPENMETADATA_PASSWORD": om_pass,
        }
        code = f"""
from phlo.hooks.emitters import (
    LineageEventContext,
    LineageEventEmitter,
    QualityResultEventContext,
    QualityResultEventEmitter,
)

source_fqn = {source_fqn!r}
target_fqn = {table_fqn!r}

LineageEventEmitter(LineageEventContext(tags={{"source": "bundled_stack_contract"}})).emit_edges(
    edges=[(source_fqn, target_fqn)],
    asset_keys=[target_fqn],
    metadata={{"bundled_stack_contract": True}},
)

QualityResultEventEmitter(
    QualityResultEventContext(asset_key=target_fqn, tags={{"source": "bundled_stack_contract"}})
).emit_result(
    check_name="bundled_stack_row_count",
    passed=True,
    check_type="CountCheck",
    metadata={{"table_fqn": target_fqn, "metric_value": {{"row_count": 1}}}},
)
"""
        self.run_python(code, env_updates=emit_env, timeout=60)
        time.sleep(2)

        lineage = self._utils().openmetadata_get_with_fallback(
            [f"{om_base_url}/api/v1/lineage/table/{table['id']}?upstreamDepth=1&downstreamDepth=0"],
            token=om_token,
            username=om_user,
            password=om_pass,
            timeout=30,
        )
        assert isinstance(lineage, dict)
        edges = lineage.get("edges") or lineage.get("upstreamEdges") or []
        assert isinstance(edges, list)
        assert edges

        test_cases = self._utils().openmetadata_get_with_fallback(
            [
                f"{om_base_url}/api/v1/dataQuality/testCases?limit=100",
                f"{om_base_url}/api/v1/testCases?limit=100",
            ],
            token=om_token,
            username=om_user,
            password=om_pass,
            timeout=30,
        )
        data = test_cases.get("data", []) if isinstance(test_cases, dict) else test_cases
        assert isinstance(data, list)
        assert any(
            table_fqn in str(case.get("entityLink", "")) for case in data if isinstance(case, dict)
        )

    def materialize(
        self,
        asset_name: str,
        *,
        partition_date: str | None = None,
        timeout: int = 1200,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Materialize a Dagster asset.

        Args:
            asset_name: Name of the asset to materialize.
            partition_date: Optional partition date for partitioned assets.
            timeout: Maximum time for materialization (seconds).
            stream_output: If True, stream output in real-time.

        Returns:
            CompletedProcess with materialization results.

        """
        args = ["materialize", asset_name]
        if partition_date is not None:
            args.extend(["--partition", partition_date])
        return self.run_phlo(args, timeout=timeout, stream_output=stream_output)

    def launch_versioned_materialization(
        self,
        asset_name: str,
        *,
        partition_date: str | None = None,
    ) -> tuple[str, str]:
        """Launch a Dagster asset run tagged to an isolated WAP branch.

        Creates a temporary Nessie branch, tags the run with the branch name,
        and submits the job to Dagster.

        Args:
            asset_name: Name of the asset to materialize.
            partition_date: Optional partition date for partitioned assets.

        Returns:
            Tuple of (run_id, branch_name).

        Raises:
            RuntimeError: If unable to create branch or launch run.

        """
        from phlo_nessie.resource import NessieResource

        logical_run_id = uuid.uuid4().hex
        branch_name = f"pipeline-run-{logical_run_id}"
        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        created_hash = nessie.create_branch(branch_name, from_ref="main")
        if created_hash is None:
            raise RuntimeError(f"Unable to create WAP branch {branch_name}")

        tags: dict[str, str] = {
            "phlo/wap_branch": branch_name,
            "phlo/run_id": logical_run_id,
            "phlo/project_id": self.project_dir.name,
            "phlo/attempt": "1",
        }
        if partition_date:
            tags[PARTITION_NAME_TAG] = partition_date

        deadline = time.time() + 60
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                run_id = self.dagster_graphql_client().submit_job_execution(
                    job_name="__ASSET_JOB",
                    run_config={},
                    asset_selection=[asset_name],
                    tags=tags,
                )
                return run_id, branch_name
            except Exception as exc:
                last_error = exc
                time.sleep(2)
        raise RuntimeError("Unable to launch Dagster versioned materialization") from last_error

    def wait_for_run_completion(self, run_id: str, *, timeout: int = 1200) -> DagsterRunStatus:
        """Poll Dagster until a launched run reaches a terminal status.

        Args:
            run_id: ID of the Dagster run to wait for.
            timeout: Maximum time to wait (seconds).

        Returns:
            Final DagsterRunStatus.

        Raises:
            RuntimeError: If run finishes with non-success status.

        """
        status = self.wait_for_run_status(
            run_id,
            expected_statuses={
                DagsterRunStatus.SUCCESS,
                DagsterRunStatus.FAILURE,
                DagsterRunStatus.CANCELED,
                DagsterRunStatus.CANCELING,
            },
            timeout=timeout,
        )
        if status != DagsterRunStatus.SUCCESS:
            raise RuntimeError(f"Dagster run {run_id} finished with status {status.value}")
        return status

    def wait_for_run_status(
        self,
        run_id: str,
        *,
        expected_statuses: set[DagsterRunStatus],
        timeout: int = 1200,
    ) -> DagsterRunStatus:
        """Poll persisted Dagster metadata until a run reaches an expected status.

        Args:
            run_id: ID of the Dagster run to wait for.
            expected_statuses: Set of statuses that indicate completion.
            timeout: Maximum time to wait (seconds).

        Returns:
            DagsterRunStatus when run reaches expected status.

        Raises:
            TimeoutError: If timeout is reached without expected status.

        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_run_status(run_id)
            if status in expected_statuses:
                return status
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for Dagster run {run_id}")

    def get_run_status(self, run_id: str) -> DagsterRunStatus:
        """Read Dagster run status from the metadata database.

        Args:
            run_id: ID of the Dagster run.

        Returns:
            Current DagsterRunStatus.

        Raises:
            RuntimeError: If run is not found in database.

        """
        env_vars = self.read_env()
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=self.ports.postgres,
            user=env_vars.get("POSTGRES_USER", "phlo"),
            password=env_vars.get("POSTGRES_PASSWORD", "phlo"),
            dbname=env_vars.get("POSTGRES_DB", "phlo"),
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM runs WHERE run_id = %s",
                    (run_id,),
                )
                row = cursor.fetchone()
        finally:
            connection.close()

        if row is None or row[0] is None:
            raise RuntimeError(f"Unable to find Dagster run {run_id}")
        return DagsterRunStatus(str(row[0]))

    def get_run_tags(self, run_id: str) -> dict[str, str]:
        """Read persisted Dagster run tags from the metadata database.

        Args:
            run_id: ID of the Dagster run.

        Returns:
            Dictionary of run tags.

        """
        env_vars = self.read_env()
        connection = psycopg2.connect(
            host="127.0.0.1",
            port=self.ports.postgres,
            user=env_vars.get("POSTGRES_USER", "phlo"),
            password=env_vars.get("POSTGRES_PASSWORD", "phlo"),
            dbname=env_vars.get("POSTGRES_DB", "phlo"),
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT key, value FROM run_tags WHERE run_id = %s",
                    (run_id,),
                )
                rows = cursor.fetchall()
        finally:
            connection.close()
        return {str(key): str(value) for key, value in rows}

    def list_table_snapshots(
        self, *, table_name: str, ref: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """List Iceberg snapshots for a table on a given ref using host-accessible settings.

        Args:
            table_name: Name of the table.
            ref: Git ref or branch name.
            limit: Maximum number of snapshots to return.

        Returns:
            List of snapshot dictionaries.

        """
        from phlo_iceberg.catalog import get_catalog, reset_catalog_cache
        from phlo_iceberg.resource import IcebergResource
        from phlo_iceberg.settings import get_settings as get_iceberg_settings

        env_vars = self.read_env()
        minio_access_key = os.environ.get(
            "PHLO_TEST_MINIO_ACCESS_KEY",
            env_vars.get("MINIO_ROOT_USER", "minio"),
        )
        minio_secret_key = os.environ.get(
            "PHLO_TEST_MINIO_SECRET_KEY",
            env_vars.get("MINIO_ROOT_PASSWORD", "minio123"),
        )
        env_updates = {
            "ICEBERG_S3_ENDPOINT": f"http://127.0.0.1:{self.ports.minio_api}",
            "ICEBERG_NESSIE_URI": f"http://127.0.0.1:{self.ports.nessie}/iceberg",
            "AWS_ACCESS_KEY_ID": minio_access_key,
            "AWS_SECRET_ACCESS_KEY": minio_secret_key,
            "ICEBERG_S3_ACCESS_KEY": minio_access_key,
            "ICEBERG_S3_SECRET_KEY": minio_secret_key,
        }
        host_file_io_properties = {
            "s3.endpoint": env_updates["ICEBERG_S3_ENDPOINT"],
            "s3.access-key-id": minio_access_key,
            "s3.secret-access-key": minio_secret_key,
        }
        previous = {key: os.environ.get(key) for key in env_updates}
        catalog = None
        original_load_file_io = None
        try:
            for key, value in env_updates.items():
                os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()
            catalog = get_catalog(ref=ref)
            original_load_file_io = catalog._load_file_io

            def load_host_file_io(
                properties: dict[str, Any] | None = None,
                location: str | None = None,
            ) -> Any:
                return original_load_file_io(
                    {**(properties or {}), **host_file_io_properties}, location
                )

            catalog._load_file_io = load_host_file_io
            resource = IcebergResource(ref=ref)
            try:
                return resource.list_snapshots(table_name=table_name, limit=limit)
            except Exception:
                return []
        finally:
            if catalog is not None and original_load_file_io is not None:
                catalog._load_file_io = original_load_file_io
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()

    def wait_for_branch_absence(self, branch_name: str, *, timeout: int = 120) -> None:
        """Wait until a promoted WAP branch is cleaned up.

        Args:
            branch_name: Name of the branch to wait for removal.
            timeout: Maximum time to wait (seconds).

        Raises:
            TimeoutError: If branch still exists after timeout.

        """
        from phlo_nessie.resource import NessieResource

        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not any(branch.name == branch_name for branch in nessie.list_branches()):
                return
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for branch cleanup: {branch_name}")

    def stop_services(
        self,
        services: list[str] | None = None,
        *,
        timeout: int = 300,
        native: bool | None = None,
        stream_output: bool = True,
    ) -> None:
        """Stop services in the bundled stack.

        Args:
            services: List of service names to stop. If None, stops all services.
            timeout: Maximum time for shutdown (seconds).
            native: If True, stop native services only. If None, stop both.
            stream_output: If True, stream output in real-time.

        """
        if services:
            args = ["services", "stop"]
            if native:
                args.append("--native")
            for service in services:
                args.extend(["--service", service])
            self.run_phlo(
                args,
                timeout=timeout,
                check=False,
                stream_output=stream_output,
            )
            return

        if native is None or native:
            with contextlib.suppress(Exception):
                self.run_phlo(
                    ["services", "stop", "--native"],
                    timeout=timeout,
                    check=False,
                    stream_output=stream_output,
                )
        if native is None or not native:
            with contextlib.suppress(Exception):
                self.run_phlo(
                    ["services", "stop"],
                    timeout=timeout,
                    check=False,
                    stream_output=stream_output,
                )

    def cleanup(
        self,
        *,
        stream_output: bool = True,
        force: bool = False,
    ) -> None:
        """Clean up the harness and all resources.

        Stops services and removes the project directory unless keep_running
        is set and force is False.

        Args:
            stream_output: If True, stream output during cleanup.
            force: If True, clean up even if keep_running is set.

        """
        if self.keep_running and not force:
            return
        utils = _load_golden_path_module()
        self.stop_services(stream_output=stream_output)
        with contextlib.suppress(Exception):
            utils.force_remove_directory(self.project_dir)


def _write_bundled_stack_workflow(
    *,
    project_dir: Path,
    python_executable: Path,
    stream_output: bool,
) -> None:
    """Write default workflow files for bundled stack testing.

    Creates sample ingestion, transformation, and publishing assets
    for testing the bundled stack.

    Args:
        project_dir: Project directory path.
        python_executable: Python executable path.
        stream_output: Whether to stream command output.

    """
    utils = _load_golden_path_module()
    env_vars = cast(dict[str, str], utils.read_env_file(project_dir / ".phlo" / ".env"))

    utils.run_phlo(
        [
            "workflow",
            "create",
            "--type",
            "ingestion",
            "--domain",
            "jsonplaceholder",
            "--table",
            "posts",
            "--unique-key",
            "id",
            "--cron",
            "0 */1 * * *",
            "--api-base-url",
            "https://jsonplaceholder.typicode.com",
            "--field",
            "userId:int",
            "--field",
            "title:str",
            "--field",
            "body:str",
        ],
        cwd=project_dir,
        timeout=60,
        stream_output=stream_output,
        python_exe=python_executable,
    )

    utils.write_file(
        project_dir / "workflows" / "ingestion" / "jsonplaceholder" / "posts.py",
        '''"""Jsonplaceholder posts ingestion asset."""\n\nimport time\n\nfrom dlt.sources.rest_api import rest_api\nfrom phlo_dlt import phlo_ingestion\nfrom workflows.schemas.jsonplaceholder import RawPosts\n\n\n@phlo_ingestion(\n    table_name="posts",\n    unique_key="id",\n    validation_schema=RawPosts,\n    group="jsonplaceholder",\n    cron="0 */1 * * *",\n    freshness_hours=(1, 24),\n    validate=True,\n)\ndef posts(partition_date: str):\n    time.sleep(2)\n    base_url = "https://jsonplaceholder.typicode.com"\n    return rest_api(\n        client={"base_url": base_url},\n        resources=[{"name": "posts", "endpoint": {"path": "posts"}}],\n    )\n''',
    )

    utils.write_file(
        project_dir / "workflows" / "transforms" / "dbt" / "profiles" / "profiles.yml",
        f"""phlo:
  target: dev
  outputs:
    dev:
      type: trino
      method: none
      user: {env_vars.get("TRINO_USER", "dagster")}
      host: trino
      port: 8080
      catalog: {env_vars.get("TRINO_CATALOG", "iceberg")}
      schema: {env_vars.get("TRINO_SCHEMA", "raw")}
      http_scheme: http
      threads: 2
""",
    )
    utils.write_file(
        project_dir / "workflows" / "transforms" / "dbt" / "models" / "sources" / "raw.yml",
        f"""version: 2\n\nsources:
  - name: raw
    database: {env_vars.get("TRINO_CATALOG", "iceberg")}
    schema: {env_vars.get("TRINO_SCHEMA", "raw")}
    tables:
      - name: posts
        columns:
          - name: id
          - name: user_id
          - name: title
          - name: body
""",
    )
    utils.write_file(
        project_dir / "workflows" / "transforms" / "dbt" / "models" / "marts" / "posts_mart.sql",
        "{{ config(materialized='table', schema='marts') }}\nselect\n  cast(src.id as varchar) as id,\n  src.user_id,\n  src.title,\n  src.body\nfrom {{ source('raw', 'posts') }} as src\n",
    )
    utils.write_file(
        project_dir / "workflows" / "publishing" / "__init__.py",
        '"""Publishing assets."""\n',
    )
    utils.write_file(
        project_dir / "workflows" / "publishing" / "jsonplaceholder.py",
        """import dagster as dg
import psycopg2
from phlo_postgres.settings import get_settings
from phlo_trino import TrinoResource
from phlo_trino.publishing import publish_marts_to_postgres


@dg.asset(
    name="publish_jsonplaceholder_marts",
    group_name="publishing",
    deps=[dg.AssetKey("posts_mart")],
)
def publish_jsonplaceholder_marts(context):
    settings = get_settings()
    trino = TrinoResource()
    postgres = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        dbname=settings.postgres_db,
    )
    try:
        return publish_marts_to_postgres(
            context=context,
            trino=trino,
            postgres=postgres,
            tables_to_publish={"posts_mart": "raw_marts.posts_mart"},
            data_source="jsonplaceholder",
        )
    finally:
        postgres.close()
""",
    )


def _wait_for_bundled_stack_services(ports: BundledStackPorts) -> None:
    """Wait for all bundled stack services to become ready.

    Polls Dagster, MinIO, Trino, Postgres, and Nessie until they respond.

    Args:
        ports: BundledStackPorts with resolved service ports.

    Raises:
        RuntimeError: If any service fails to become ready.

    """
    utils = _load_golden_path_module()
    if not utils.wait_for_tcp("127.0.0.1", ports.dagster, name="Dagster", timeout=120):
        raise RuntimeError("Dagster did not become ready")
    if not utils.wait_for_http(
        f"http://127.0.0.1:{ports.minio_api}/minio/health/live",
        name="MinIO",
        timeout=60,
    ):
        raise RuntimeError("MinIO did not become ready")
    if not utils.wait_for_http(
        f"http://127.0.0.1:{ports.trino}/v1/info",
        name="Trino",
        timeout=120,
    ):
        raise RuntimeError("Trino did not become ready")
    if not utils.wait_for_tcp("127.0.0.1", ports.postgres, name="Postgres", timeout=120):
        raise RuntimeError("Postgres did not become ready")
    if not utils.wait_for_tcp("127.0.0.1", ports.nessie, name="Nessie", timeout=120):
        raise RuntimeError("Nessie did not become ready")
    _wait_for_dagster_graphql(ports)


def _wait_for_dagster_graphql(ports: BundledStackPorts, *, timeout: int = 180) -> None:
    """Wait until Dagster GraphQL is responsive.

    Args:
        ports: BundledStackPorts with resolved service ports.
        timeout: Maximum time to wait (seconds).

    Raises:
        RuntimeError: If Dagster GraphQL doesn't become ready.

    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.post(
                f"http://127.0.0.1:{ports.dagster}/graphql",
                json={"query": "query Version { version }"},
                timeout=5,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("data", {}).get("version"):
                return
        except Exception:
            time.sleep(1)
            continue
    raise RuntimeError("Dagster GraphQL did not become ready")


def bootstrap_bundled_stack_harness(
    *,
    project_dir: Path | None = None,
    stream_output: bool = True,
    keep_running: bool | None = None,
) -> BundledStackHarness:
    """Create a real project, boot the bundled stack, and return a harness.

    This is the main entry point for bundled stack contract testing. It:
    1. Creates a temporary project directory
    2. Initializes a Phlo project
    3. Starts core services (Postgres, MinIO, Nessie, Trino, Dagster)
    4. Waits for services to be ready
    5. Returns a BundledStackHarness for test interaction

    Args:
        project_dir: Optional project directory path. If None, creates a temp directory.
        stream_output: Whether to stream command output during setup.
        keep_running: Whether to keep services running after tests. If None,
            uses the PHLO_KEEP_BUNDLED_STACK environment variable.

    Returns:
        BundledStackHarness ready for testing.

    Raises:
        RuntimeError: If Docker is unavailable or setup fails.

    Example:
        >>> harness = bootstrap_bundled_stack_harness()
        >>> harness.materialize("posts", partition_date="2024-01-01")
        >>> harness.verify_api_stack()
        >>> harness.cleanup()

    """
    utils = _load_golden_path_module()
    phlo_source = _repo_root()
    target_project_dir = project_dir or default_bundled_stack_project_dir()
    should_keep_running = keep_bundled_stack_running() if keep_running is None else keep_running

    docker_info = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if docker_info.returncode != 0:
        raise RuntimeError("Docker daemon is unavailable for bundled-stack contract tests")

    _cleanup_existing_bundled_stack_projects(target_project_dir.parent, stream_output=stream_output)
    _verify_bind_mount_parent(target_project_dir.parent)

    if target_project_dir.exists() and not utils.force_remove_directory(target_project_dir):
        raise RuntimeError(f"Unable to remove existing contract test project: {target_project_dir}")

    project_name = target_project_dir.name

    try:
        _run_repo_phlo(
            ["init", project_name, "--template", "basic", "--force"],
            cwd=target_project_dir.parent,
            timeout=120,
            stream_output=stream_output,
        )
        python_executable = Path(utils.setup_project_venv(target_project_dir, phlo_source))
        utils.run_phlo(
            ["services", "init", "--dev", "--phlo-source", str(phlo_source), "--force"],
            cwd=target_project_dir,
            timeout=180,
            stream_output=stream_output,
            python_exe=python_executable,
        )
        utils.apply_env_updates(
            target_project_dir / ".phlo",
            build_bundled_stack_env_updates(utils.resolve_port, project_name=project_name),
        )
        _write_bundled_stack_workflow(
            project_dir=target_project_dir,
            python_executable=python_executable,
            stream_output=stream_output,
        )
        start_args = ["services", "start"]
        for service_name in BUNDLED_STACK_CORE_SERVICES:
            start_args.extend(["--service", service_name])
        utils.run_phlo(
            start_args,
            cwd=target_project_dir,
            timeout=600,
            stream_output=stream_output,
            python_exe=python_executable,
        )

        env_vars = cast(dict[str, str], utils.read_env_file(target_project_dir / ".phlo" / ".env"))
        ports = BundledStackPorts.from_env(env_vars)
        _wait_for_bundled_stack_services(ports)
        return BundledStackHarness(
            project_dir=target_project_dir,
            phlo_source=phlo_source,
            python_executable=python_executable,
            ports=ports,
            keep_running=should_keep_running,
        )
    except Exception:
        if not should_keep_running:
            with contextlib.suppress(Exception):
                utils.run_phlo(
                    ["services", "stop"],
                    cwd=target_project_dir,
                    timeout=300,
                    check=False,
                    stream_output=stream_output,
                    python_exe=target_project_dir / ".venv" / "bin" / "python",
                )
            with contextlib.suppress(Exception):
                utils.force_remove_directory(target_project_dir)
        raise


__all__ = [
    "BUNDLED_STACK_CORE_SERVICES",
    "BUNDLED_STACK_DEV_PACKAGES",
    "BundledStackHarness",
    "BundledStackPorts",
    "bootstrap_bundled_stack_harness",
    "build_bundled_stack_env_updates",
    "bundled_stack_contract_enabled",
    "default_bundled_stack_project_dir",
    "keep_bundled_stack_running",
]
