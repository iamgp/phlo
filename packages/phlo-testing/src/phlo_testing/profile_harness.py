"""Reusable profile-level test harnesses for real Phlo service stacks."""

from __future__ import annotations

import contextlib
import importlib.util
import os
import socket
import subprocess
import sys
import time
import uuid
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

BUNDLED_STACK_DEV_PACKAGES = (
    "phlo-dagster",
    "phlo-dlt",
    "phlo-dbt",
    "phlo-iceberg",
    "phlo-trino",
    "phlo-postgres",
    "phlo-nessie",
    "phlo-minio",
    "phlo-hasura",
    "phlo-postgrest",
    "phlo-superset",
    "phlo-api",
    "phlo-observatory",
    "phlo-lineage",
)

_BUNDLED_STACK_PORT_DEFAULTS = {
    "PHLO_API_PORT": ("Phlo API", 54000),
    "DAGSTER_PORT": ("Dagster", 3000),
    "OBSERVATORY_PORT": ("Observatory", 3001),
    "POSTGRES_PORT": ("Postgres", 5432),
    "TRINO_PORT": ("Trino", 8080),
    "MINIO_API_PORT": ("MinIO API", 9000),
    "MINIO_CONSOLE_PORT": ("MinIO Console", 9001),
    "NESSIE_PORT": ("Nessie", 19120),
}

_GOLDEN_PATH_MODULE: Any | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_golden_path_module() -> Any:
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
    repo_python = _repo_root() / ".venv" / "bin" / "python"
    if repo_python.exists():
        return repo_python
    return Path(sys.executable)


def _repo_pythonpath() -> str:
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
    value = os.environ.get("PHLO_RUN_BUNDLED_STACK_CONTRACT", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def keep_bundled_stack_running() -> bool:
    value = os.environ.get("PHLO_KEEP_BUNDLED_STACK", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def default_bundled_stack_project_dir(base_dir: Path | None = None) -> Path:
    root = base_dir or (_repo_root() / ".tmp")
    return root / f"phlo-bundled-stack-{uuid.uuid4().hex[:8]}"


def _port_in_use(port: int) -> bool:
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
    candidate = int(resolve_port(service_name, default_port))
    while candidate in used_ports or _port_in_use(candidate):
        candidate += 1
    used_ports.add(candidate)
    return candidate


def build_bundled_stack_env_updates(resolve_port: Any) -> dict[str, str]:
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
    updates["PHLO_WAP_BRANCH_CREATION_INTERVAL_SECONDS"] = "1"
    updates["PHLO_WAP_PROMOTION_INTERVAL_SECONDS"] = "1"
    return updates


def _verify_bind_mount_parent(path: Path, *, attempts: int = 5, delay_seconds: float = 0.5) -> None:
    """Verify Docker can read a marker file from the target parent path."""
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
    """Resolved host ports for the bundled-stack contract harness."""

    phlo_api: int
    dagster: int
    postgres: int
    trino: int
    minio_api: int
    minio_console: int
    nessie: int

    @classmethod
    def from_env(cls, env_vars: dict[str, str]) -> BundledStackPorts:
        return cls(
            phlo_api=int(env_vars.get("PHLO_API_PORT", "54000")),
            dagster=int(env_vars.get("DAGSTER_PORT", "3000")),
            postgres=int(env_vars.get("POSTGRES_PORT", "5432")),
            trino=int(env_vars.get("TRINO_PORT", "8080")),
            minio_api=int(env_vars.get("MINIO_API_PORT", "9000")),
            minio_console=int(env_vars.get("MINIO_CONSOLE_PORT", "9001")),
            nessie=int(env_vars.get("NESSIE_PORT", "19120")),
        )


@dataclass(slots=True)
class BundledStackHarness:
    """Runtime handle for a real bundled-stack contract environment."""

    project_dir: Path
    phlo_source: Path
    python_executable: Path
    ports: BundledStackPorts
    keep_running: bool = False

    def dagster_graphql_client(self) -> DagsterGraphQLClient:
        """Return a Dagster GraphQL client for the live harness."""
        return DagsterGraphQLClient("127.0.0.1", port_number=self.ports.dagster)

    def run_phlo(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
        check: bool = True,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
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
        utils = _load_golden_path_module()
        return cast(dict[str, str], utils.read_env_file(self.project_dir / ".phlo" / ".env"))

    def default_partition_date(self) -> str:
        return (datetime.now(UTC).date() - timedelta(days=1)).isoformat()

    def materialize(
        self,
        asset_name: str,
        *,
        partition_date: str | None = None,
        timeout: int = 1200,
        stream_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
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
        """Launch a Dagster asset run tagged to an isolated WAP branch."""
        from phlo_nessie.resource import NessieResource

        branch_name = f"pipeline-run-{uuid.uuid4().hex[:12]}"
        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        created_hash = nessie.create_branch(branch_name, from_ref="main")
        if created_hash is None:
            raise RuntimeError(f"Unable to create WAP branch {branch_name}")

        tags: dict[str, str] = {"phlo/wap_branch": branch_name}
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
        """Poll Dagster until a launched run reaches a terminal status."""
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
        """Poll persisted Dagster metadata until a run reaches an expected status."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_run_status(run_id)
            if status in expected_statuses:
                return status
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for Dagster run {run_id}")

    def get_run_status(self, run_id: str) -> DagsterRunStatus:
        """Read Dagster run status from the metadata database."""
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
        """Read persisted Dagster run tags from the metadata database."""
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
        """List Iceberg snapshots for a table on a given ref using host-accessible settings."""
        from phlo_iceberg.catalog import reset_catalog_cache
        from phlo_iceberg.resource import IcebergResource
        from phlo_iceberg.settings import get_settings as get_iceberg_settings

        env_updates = {
            "ICEBERG_S3_ENDPOINT": f"http://127.0.0.1:{self.ports.minio_api}",
            "ICEBERG_NESSIE_URI": f"http://127.0.0.1:{self.ports.nessie}/iceberg",
            "AWS_ACCESS_KEY_ID": "minio",
            "AWS_SECRET_ACCESS_KEY": "minio123",
            "ICEBERG_S3_ACCESS_KEY": "minio",
            "ICEBERG_S3_SECRET_KEY": "minio123",
        }
        previous = {key: os.environ.get(key) for key in env_updates}
        try:
            for key, value in env_updates.items():
                os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()
            resource = IcebergResource(ref=ref)
            try:
                return resource.list_snapshots(table_name=table_name, limit=limit)
            except Exception:
                return []
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            get_iceberg_settings.cache_clear()
            reset_catalog_cache()

    def wait_for_branch_absence(self, branch_name: str, *, timeout: int = 120) -> None:
        """Wait until a promoted WAP branch is cleaned up."""
        from phlo_nessie.resource import NessieResource

        nessie = NessieResource(base_url=f"http://127.0.0.1:{self.ports.nessie}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not any(branch.name == branch_name for branch in nessie.list_branches()):
                return
            time.sleep(1)
        raise TimeoutError(f"Timed out waiting for branch cleanup: {branch_name}")

    def stop_services(self, *, stream_output: bool = True) -> None:
        with contextlib.suppress(Exception):
            self.run_phlo(
                ["services", "stop"],
                timeout=300,
                check=False,
                stream_output=stream_output,
            )

    def cleanup(
        self,
        *,
        stream_output: bool = True,
        force: bool = False,
    ) -> None:
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
        f"""phlo:\n  target: dev\n  outputs:\n    dev:\n      type: trino\n      method: none\n      user: {env_vars.get("TRINO_USER", "dagster")}\n      host: trino\n      port: 8080\n      catalog: {env_vars.get("TRINO_CATALOG", "iceberg")}\n      schema: {env_vars.get("TRINO_SCHEMA", "raw")}\n      http_scheme: http\n      threads: 2\n""",
    )
    utils.write_file(
        project_dir / "workflows" / "transforms" / "dbt" / "models" / "sources" / "raw.yml",
        f"""version: 2\n\nsources:\n  - name: raw\n    database: {env_vars.get("TRINO_CATALOG", "iceberg")}\n    schema: {env_vars.get("TRINO_SCHEMA", "raw")}\n    tables:\n      - name: posts\n        columns:\n          - name: id\n          - name: user_id\n          - name: title\n          - name: body\n""",
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
        """import dagster as dg\nimport psycopg2\nfrom phlo_postgres.settings import get_settings\nfrom phlo_trino import TrinoResource\nfrom phlo_trino.publishing import publish_marts_to_postgres\n\n\n@dg.asset(\n    name="publish_jsonplaceholder_marts",\n    group_name="publishing",\n    deps=[dg.AssetKey(\"posts_mart\")],\n)\ndef publish_jsonplaceholder_marts(context):\n    settings = get_settings()\n    trino = TrinoResource()\n    postgres = psycopg2.connect(\n        host=settings.postgres_host,\n        port=settings.postgres_port,\n        user=settings.postgres_user,\n        password=settings.postgres_password,\n        dbname=settings.postgres_db,\n    )\n    try:\n        return publish_marts_to_postgres(\n            context=context,\n            trino=trino,\n            postgres=postgres,\n            tables_to_publish={\"posts_mart\": \"raw_marts.posts_mart\"},\n            data_source=\"jsonplaceholder\",\n        )\n    finally:\n        postgres.close()\n""",
    )


def _wait_for_bundled_stack_services(ports: BundledStackPorts) -> None:
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
    """Wait until Dagster GraphQL is responsive."""
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
    """Create a real project, boot the bundled stack, and return a harness."""
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
            build_bundled_stack_env_updates(utils.resolve_port),
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
