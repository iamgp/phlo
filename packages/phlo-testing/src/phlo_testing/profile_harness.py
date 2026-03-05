"""Reusable profile-level test harnesses for real Phlo service stacks."""

from __future__ import annotations

import contextlib
import importlib.util
import os
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

BUNDLED_STACK_CORE_SERVICES = (
    "postgres",
    "minio",
    "minio-setup",
    "nessie",
    "trino",
    "dagster",
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


def bundled_stack_contract_enabled() -> bool:
    value = os.environ.get("PHLO_RUN_BUNDLED_STACK_CONTRACT", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def keep_bundled_stack_running() -> bool:
    value = os.environ.get("PHLO_KEEP_BUNDLED_STACK", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def default_bundled_stack_project_dir(base_dir: Path | None = None) -> Path:
    root = base_dir or (Path.home() / "tmp")
    return root / f"phlo-bundled-stack-{uuid.uuid4().hex[:8]}"


def build_bundled_stack_env_updates(resolve_port: Any) -> dict[str, str]:
    updates = {
        env_key: str(resolve_port(service_name, default_port))
        for env_key, (service_name, default_port) in _BUNDLED_STACK_PORT_DEFAULTS.items()
    }
    updates["PHLO_DEV_EXTRA_PACKAGES"] = ",".join(BUNDLED_STACK_DEV_PACKAGES)
    return updates


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

    def stop_services(self, *, stream_output: bool = True) -> None:
        with contextlib.suppress(Exception):
            self.run_phlo(
                ["services", "stop"],
                timeout=300,
                check=False,
                stream_output=stream_output,
            )

    def cleanup(self, *, stream_output: bool = True) -> None:
        if self.keep_running:
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
        '''"""Jsonplaceholder posts ingestion asset."""\n\nfrom dlt.sources.rest_api import rest_api\nfrom phlo_dlt import phlo_ingestion\nfrom workflows.schemas.jsonplaceholder import RawPosts\n\n\n@phlo_ingestion(\n    table_name="posts",\n    unique_key="id",\n    validation_schema=RawPosts,\n    group="jsonplaceholder",\n    cron="0 */1 * * *",\n    freshness_hours=(1, 24),\n    validate=False,\n)\ndef posts(partition_date: str):\n    base_url = "https://jsonplaceholder.typicode.com"\n    return rest_api(\n        client={"base_url": base_url},\n        resources=[{"name": "posts", "endpoint": {"path": "posts"}}],\n    )\n''',
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

    bind_mount_ok, bind_mount_detail = utils.verify_bind_mount_visibility(target_project_dir.parent)
    if not bind_mount_ok:
        raise RuntimeError(
            "Docker cannot bind-mount the contract test project directory: "
            f"{target_project_dir.parent} ({bind_mount_detail})"
        )

    if target_project_dir.exists() and not utils.force_remove_directory(target_project_dir):
        raise RuntimeError(f"Unable to remove existing contract test project: {target_project_dir}")

    project_name = target_project_dir.name

    try:
        utils.run_phlo(
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
