from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

E2E_FLAG = "PHLO_E2E"
E2E_MODE_ENV = "PHLO_E2E_MODE"
E2E_SOURCE_ENV = "PHLO_E2E_PHLO_SOURCE"


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    check: bool = True,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            "\n".join(
                [
                    f"$ {' '.join(args)}",
                    "",
                    "STDOUT:",
                    result.stdout,
                    "",
                    "STDERR:",
                    result.stderr,
                ]
            )
        )
    if check and result.returncode != 0:
        raise AssertionError(
            "Command failed.\n"
            f"cwd: {cwd}\n"
            f"cmd: {' '.join(args)}\n"
            f"exit: {result.returncode}\n"
            + (f"log: {log_path}\n" if log_path else "")
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def _run_phlo(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    check: bool = True,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [sys.executable, "-m", "phlo.cli.main", *args],
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=check,
        log_path=log_path,
    )


def _read_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _wait_for_compose_service(
    *,
    project: str,
    service: str,
    timeout_seconds: int = 300,
) -> None:
    deadline = time.time() + timeout_seconds
    last_status = "unknown"
    while time.time() < deadline:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-q",
                "--filter",
                f"label=com.docker.compose.project={project}",
                "--filter",
                f"label=com.docker.compose.service={service}",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        container_id = result.stdout.strip()
        if container_id:
            inspect = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                    container_id,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            last_status = inspect.stdout.strip()
            if last_status in {"healthy", "running"}:
                return
            if last_status in {"exited", "dead", "unhealthy"}:
                raise AssertionError(
                    f"Service {service} failed to start (status={last_status})."
                )
        time.sleep(2)
    raise AssertionError(f"Timed out waiting for {service}. Last status: {last_status}")


def _ensure_docker_running() -> None:
    result = subprocess.run(
        ["docker", "info"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("Docker is not available or not running.")


def _fix_ownership(path: Path) -> None:
    if not path.exists():
        return
    uid = os.getuid()
    gid = os.getgid()
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{path}:/work",
            "alpine",
            "sh",
            "-c",
            f"chown -R {uid}:{gid} /work || true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def _require_e2e_flag() -> None:
    if os.environ.get(E2E_FLAG, "").lower() not in {"1", "true", "yes"}:
        pytest.skip(f"Set {E2E_FLAG}=1 to run the golden-path E2E test.")


def _resolve_phlo_source() -> Path | None:
    override = os.environ.get(E2E_SOURCE_ENV)
    if override:
        path = Path(override).expanduser().resolve()
        if path.exists():
            return path
        return None

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "pyproject.toml").exists() and (repo_root / "src" / "phlo").exists():
        return repo_root
    return None


def _ensure_materialize_command(project_dir: Path) -> None:
    result = _run_phlo(["materialize", "--help"], cwd=project_dir, check=False)
    if result.returncode != 0:
        pytest.skip("phlo materialize command not available (install phlo-dagster).")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_jsonplaceholder_asset(asset_file: Path) -> None:
    content = textwrap.dedent(
        """
        \"\"\"
        Jsonplaceholder posts ingestion asset.
        \"\"\"

        from dlt.sources.rest_api import rest_api

        from phlo_dlt import phlo_ingestion
        from workflows.schemas.jsonplaceholder import RawPosts


        @phlo_ingestion(
            table_name="posts",
            unique_key="id",
            validation_schema=RawPosts,
            group="jsonplaceholder",
            cron="0 */1 * * *",
            freshness_hours=(1, 24),
            validate=False,
        )
        def posts(partition_date: str):
            start_time = f\"{partition_date}T00:00:00.000Z\"
            end_time = f\"{partition_date}T23:59:59.999Z\"
            base_url = "https://jsonplaceholder.typicode.com"

            return rest_api(
                client={"base_url": base_url},
                resources=[
                    {
                        "name": "posts",
                        "endpoint": {
                            "path": "posts",
                            "params": {
                                "start_date": start_time,
                                "end_date": end_time,
                            },
                        },
                    }
                ],
            )
        """
    ).lstrip()
    _write_text(asset_file, content)


def test_golden_path_e2e(tmp_path: Path) -> None:
    _require_e2e_flag()
    _ensure_docker_running()
    mode = os.environ.get(E2E_MODE_ENV, "dev").strip().lower()
    if mode not in {"dev", "pypi"}:
        pytest.skip(f"{E2E_MODE_ENV} must be 'dev' or 'pypi'.")
    try:
        from trino.dbapi import connect as trino_connect  # noqa: F401
    except ImportError:
        pytest.skip("Trino client not installed (install phlo-trino/dbt-trino).")

    project_name = "phlo-golden-path"
    project_dir = tmp_path / project_name
    log_dir = tmp_path / "e2e-logs"
    step_counter = 0

    def _log_for(step: str) -> Path:
        nonlocal step_counter
        step_counter += 1
        safe_step = step.replace(" ", "_").replace("/", "_")
        return log_dir / f"{step_counter:02d}-{safe_step}.log"

    def run_phlo_step(name: str, args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        return _run_phlo(args, cwd=project_dir, log_path=_log_for(name), **kwargs)

    _run_phlo(
        ["init", project_name, "--template", "basic"],
        cwd=tmp_path,
        timeout=120,
        log_path=_log_for("phlo_init"),
    )

    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "workflows").is_dir()
    assert (project_dir / "workflows" / "ingestion").is_dir()
    assert (project_dir / "workflows" / "schemas").is_dir()
    assert (project_dir / "transforms" / "dbt" / "dbt_project.yml").exists()

    if mode == "dev":
        phlo_source = _resolve_phlo_source()
        if not phlo_source:
            pytest.skip(
                "PHLO_E2E_MODE=dev requires a local phlo checkout. "
                f"Set {E2E_SOURCE_ENV}=/path/to/phlo."
            )
        run_phlo_step(
            "services_init_dev",
            ["services", "init", "--dev", "--phlo-source", str(phlo_source), "--force"],
            timeout=180,
        )
    else:
        run_phlo_step(
            "services_init_pypi",
            ["services", "init", "--no-dev", "--force"],
            timeout=180,
        )

    phlo_dir = project_dir / ".phlo"
    assert (project_dir / "phlo.yaml").exists()
    assert (phlo_dir / "docker-compose.yml").exists()
    assert (phlo_dir / ".env").exists()
    assert (phlo_dir / ".env.local").exists()
    assert (phlo_dir / ".gitignore").exists()
    assert (phlo_dir / "volumes").is_dir()

    run_phlo_step(
        "create_workflow",
        [
            "create-workflow",
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
        timeout=60,
    )

    schema_file = project_dir / "workflows" / "schemas" / "jsonplaceholder.py"
    asset_file = (
        project_dir
        / "workflows"
        / "ingestion"
        / "jsonplaceholder"
        / "posts.py"
    )
    assert schema_file.exists()
    assert asset_file.exists()
    assert "jsonplaceholder.typicode.com" in asset_file.read_text()
    _write_jsonplaceholder_asset(asset_file)

    _write_text(
        project_dir / "transforms" / "dbt" / "profiles" / "profiles.yml",
        textwrap.dedent(
            """
            phlo:
              target: dev
              outputs:
                dev:
                  type: trino
                  method: none
                  user: dagster
                  host: trino
                  port: 8080
                  catalog: iceberg
                  schema: raw
                  http_scheme: http
                  threads: 2
            """
        ).lstrip(),
    )

    _write_text(
        project_dir / "transforms" / "dbt" / "models" / "marts" / "posts_mart.sql",
        textwrap.dedent(
            """
            {{ config(materialized='table', schema='marts') }}

            select
              cast(id as varchar) as id,
              user_id,
              title,
              body
            from iceberg.raw.posts
            """
        ).lstrip(),
    )

    _write_text(
        project_dir / "workflows" / "publishing" / "__init__.py",
        '"""Publishing assets."""\n',
    )

    _write_text(
        project_dir / "workflows" / "publishing" / "jsonplaceholder.py",
        textwrap.dedent(
            """
            import dagster as dg
            import psycopg2

            from phlo.config import get_settings
            from phlo.publishing import publish_marts_to_postgres
            from phlo_trino import TrinoResource


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
                        tables_to_publish={"posts_mart": "iceberg.marts.posts_mart"},
                        data_source="jsonplaceholder",
                    )
                finally:
                    postgres.close()
            """
        ).lstrip(),
    )

    _ensure_materialize_command(project_dir)

    services_to_start = [
        "postgres",
        "minio",
        "minio-setup",
        "nessie",
        "trino",
        "dagster",
    ]
    stop_args = ["services", "stop"]
    for name in services_to_start:
        stop_args.extend(["--service", name])

    try:
        start_args = ["services", "start"]
        for name in services_to_start:
            start_args.extend(["--service", name])
        run_phlo_step("services_start_core", start_args, timeout=600)

        project = project_name
        for service in ["postgres", "minio", "nessie", "trino", "dagster"]:
            _wait_for_compose_service(project=project, service=service, timeout_seconds=420)

        run_phlo_step(
            "materialize_dlt_posts",
            ["materialize", "dlt_posts", "--partition", "2025-01-01"],
            timeout=1200,
        )

        env_vars = _read_env_file(phlo_dir / ".env")
        trino_port = int(env_vars.get("TRINO_PORT", "8080"))
        postgres_port = int(env_vars.get("POSTGRES_PORT", "5432"))
        postgres_user = env_vars.get("POSTGRES_USER", "phlo")
        postgres_password = env_vars.get("POSTGRES_PASSWORD", "phlo")
        postgres_db = env_vars.get("POSTGRES_DB", "phlo")

        from phlo_trino import TrinoResource

        trino = TrinoResource(host="localhost", port=trino_port, catalog="iceberg")
        trino.wait_ready(timeout=180, interval=2, schema="raw")
        rows = trino.execute("SELECT count(*) FROM posts", schema="raw")
        assert rows and rows[0][0] > 0

        run_phlo_step(
            "materialize_posts_mart",
            ["materialize", "posts_mart", "--partition", "2025-01-01"],
            timeout=1200,
        )

        rows = trino.execute("SELECT count(*) FROM posts_mart", schema="marts")
        assert rows and rows[0][0] > 0

        run_phlo_step(
            "materialize_publish_marts",
            ["materialize", "publish_jsonplaceholder_marts", "--partition", "2025-01-01"],
            timeout=1200,
        )

        import psycopg2

        pg_conn = psycopg2.connect(
            host="localhost",
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            dbname=postgres_db,
        )
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM marts.posts_mart")
                rows = cursor.fetchall()
                assert rows and rows[0][0] > 0
        finally:
            pg_conn.close()

        services = json.loads(
            _run_phlo(["services", "list", "--all", "--json"], cwd=project_dir).stdout
        )
        optional = sorted(
            {
                service["name"]
                for service in services
                if not service.get("default") and not service.get("inline")
            }
        )

        observability = [
            name
            for name in ["loki", "prometheus", "grafana", "alloy"]
            if name in optional
        ]
        for name in observability:
            run_phlo_step(f"services_add_{name}", ["services", "add", name, "--no-start"], timeout=120)
            optional.remove(name)

        compose = yaml.safe_load((phlo_dir / "docker-compose.yml").read_text())
        services_block = compose.get("services", {})
        assert set(observability).issubset(set(services_block))

        grafana_deps = services_block.get("grafana", {}).get("depends_on", {})
        assert {"prometheus", "loki"}.issubset(set(grafana_deps.keys()))

        alloy_deps = services_block.get("alloy", {}).get("depends_on", {})
        assert "loki" in alloy_deps

        grafana_datasources = (
            phlo_dir / "grafana" / "provisioning" / "datasources" / "datasources.yml"
        ).read_text()
        assert "http://prometheus:9090" in grafana_datasources
        assert "http://loki:3100" in grafana_datasources

        prometheus_config = (phlo_dir / "prometheus" / "prometheus.yml").read_text()
        assert "phlo.metrics.enabled" in prometheus_config

        alloy_config = (phlo_dir / "alloy" / "config.alloy").read_text()
        assert "http://loki:3100/loki/api/v1/push" in alloy_config

        for name in optional:
            run_phlo_step(f"services_add_{name}", ["services", "add", name, "--no-start"], timeout=120)

        enabled_config = yaml.safe_load((project_dir / "phlo.yaml").read_text())
        enabled = set(enabled_config.get("services", {}).get("enabled", []))
        assert enabled.issuperset(set(observability))
        assert enabled.issuperset(set(optional))
    finally:
        _run_phlo(stop_args, cwd=project_dir, timeout=300, check=False)
        _fix_ownership(project_dir)
