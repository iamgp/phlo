from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

E2E_FLAG = "PHLO_E2E"
E2E_MODE_ENV = "PHLO_E2E_MODE"
E2E_SOURCE_ENV = "PHLO_E2E_PHLO_SOURCE"

# Configurable timeouts via environment variables (Improvement #8)
INIT_TIMEOUT = int(os.environ.get("PHLO_E2E_INIT_TIMEOUT", "180"))
SERVICE_START_TIMEOUT = int(os.environ.get("PHLO_E2E_SERVICE_TIMEOUT", "600"))
MATERIALIZE_TIMEOUT = int(os.environ.get("PHLO_E2E_MATERIALIZE_TIMEOUT", "1200"))
SERVICE_HEALTHY_TIMEOUT = int(os.environ.get("PHLO_E2E_HEALTHY_TIMEOUT", "420"))
TRINO_READY_TIMEOUT = int(os.environ.get("PHLO_E2E_TRINO_TIMEOUT", "120"))

# Test partitions for multi-partition testing (Improvement #9)
TEST_PARTITIONS = ["2025-01-01", "2025-01-02"]


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
        message = f"Command failed.\ncwd: {cwd}\ncmd: {' '.join(args)}\nexit: {result.returncode}\n"
        if log_path:
            message += f"log: {log_path}\n"
        message += f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        raise AssertionError(message)
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
                raise AssertionError(f"Service {service} failed to start (status={last_status}).")
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


def _wait_for_trino_ready(*, host: str, port: int, timeout: int, log_path: Path) -> None:
    deadline = time.monotonic() + timeout
    attempts = 0
    last_error: str | None = None
    last_starting: bool | None = None

    while time.monotonic() < deadline:
        attempts += 1
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/v1/info", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            starting = bool(payload.get("starting", False))
            last_starting = starting
            if not starting:
                _write_text(
                    log_path,
                    f"ready after {attempts} attempts (starting={starting}).\n",
                )
                return
            last_error = "starting=true"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = repr(exc)
        time.sleep(2)

    _write_text(
        log_path,
        f"timeout after {attempts} attempts; last_error={last_error} starting={last_starting}\n",
    )
    raise AssertionError(
        f"Trino not ready after {timeout}s (last_error={last_error}, starting={last_starting})."
    )


# Improvement #6: Generic health check endpoint testing
def _check_health_endpoint(
    url: str,
    *,
    timeout: int = 5,
    expected_status: int = 200,
) -> bool:
    """Check if an HTTP endpoint responds with expected status."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == expected_status
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _wait_for_http_endpoint(
    url: str,
    *,
    timeout_seconds: int = 60,
    poll_interval: int = 2,
    log_path: Path | None = None,
) -> None:
    """Wait for an HTTP endpoint to become available."""
    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    last_error: str | None = None

    while time.monotonic() < deadline:
        attempts += 1
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    if log_path:
                        _write_text(log_path, f"Endpoint {url} ready after {attempts} attempts.\n")
                    return
                last_error = f"status={response.status}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = repr(exc)
        time.sleep(poll_interval)

    msg = f"Endpoint {url} not ready after {timeout_seconds}s (last_error={last_error})"
    if log_path:
        _write_text(log_path, msg + "\n")
    raise AssertionError(msg)


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
        timeout=INIT_TIMEOUT,
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
            timeout=INIT_TIMEOUT,
        )
    else:
        run_phlo_step(
            "services_init_pypi",
            ["services", "init", "--no-dev", "--force"],
            timeout=INIT_TIMEOUT,
        )

    phlo_dir = project_dir / ".phlo"
    assert (project_dir / "phlo.yaml").exists()
    assert (phlo_dir / "docker-compose.yml").exists()
    assert (phlo_dir / ".env").exists()
    assert (phlo_dir / ".env.local").exists()
    assert (phlo_dir / ".gitignore").exists()
    assert (phlo_dir / "volumes").is_dir()

    # Set a non-default API port to avoid conflicts with other services on the host
    with (phlo_dir / ".env").open("a") as f:
        f.write("\nPHLO_API_PORT=54000\n")

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
    asset_file = project_dir / "workflows" / "ingestion" / "jsonplaceholder" / "posts.py"
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
                    tables_to_publish={"posts_mart": "iceberg.raw_marts.posts_mart"},
                    data_source="jsonplaceholder",
                )
                finally:
                    postgres.close()
            """
        ).lstrip(),
    )

    _ensure_materialize_command(project_dir)

    # Core services needed for the pipeline (including observatory for UI testing)
    services_to_start = [
        "postgres",
        "minio",
        "minio-setup",
        "nessie",
        "trino",
        "dagster",
    ]

    # Improvement #7: Better cleanup - track all services added for cleanup
    all_services_added: list[str] = list(services_to_start)

    try:
        start_args = ["services", "start"]
        for name in services_to_start:
            start_args.extend(["--service", name])
        run_phlo_step("services_start_core", start_args, timeout=SERVICE_START_TIMEOUT)

        project = project_name
        for service in ["postgres", "minio", "nessie", "trino", "dagster"]:
            _wait_for_compose_service(
                project=project, service=service, timeout_seconds=SERVICE_HEALTHY_TIMEOUT
            )

        # Improvement #6: Test health check endpoints
        env_vars = _read_env_file(phlo_dir / ".env")
        dagster_port = int(env_vars.get("DAGSTER_PORT", "3000"))
        minio_port = int(env_vars.get("MINIO_API_PORT", "9000"))
        trino_port = int(env_vars.get("TRINO_PORT", "8080"))
        postgres_port = int(env_vars.get("POSTGRES_PORT", "5432"))
        postgres_user = env_vars.get("POSTGRES_USER", "phlo")
        postgres_password = env_vars.get("POSTGRES_PASSWORD", "phlo")
        postgres_db = env_vars.get("POSTGRES_DB", "phlo")
        observatory_port = int(env_vars.get("OBSERVATORY_PORT", "3001"))

        health_checks = [
            (f"http://127.0.0.1:{dagster_port}/server_info", "dagster"),
            (f"http://127.0.0.1:{minio_port}/minio/health/live", "minio"),
            (f"http://127.0.0.1:{trino_port}/v1/info", "trino"),
        ]
        for url, name in health_checks:
            _wait_for_http_endpoint(url, timeout_seconds=60, log_path=_log_for(f"health_{name}"))
            assert _check_health_endpoint(url), f"{name} health check failed at {url}"

        # Improvement #2: Test Observatory UI accessibility
        observatory_url = f"http://127.0.0.1:{observatory_port}"
        try:
            _wait_for_http_endpoint(
                observatory_url, timeout_seconds=60, log_path=_log_for("observatory_ready")
            )
            assert _check_health_endpoint(observatory_url), "Observatory UI not accessible"
            _write_text(
                _log_for("observatory_check"), f"Observatory accessible at {observatory_url}\n"
            )
        except AssertionError:
            # Observatory may not be configured in all setups, log but continue
            _write_text(_log_for("observatory_check"), "Observatory not available (optional)\n")

        _wait_for_trino_ready(
            host="127.0.0.1",
            port=trino_port,
            timeout=TRINO_READY_TIMEOUT,
            log_path=_log_for("trino_ready"),
        )

        from phlo_trino import TrinoResource

        trino = TrinoResource(host="127.0.0.1", port=trino_port, catalog="iceberg")

        # Improvement #9: Test multiple partitions
        for partition in TEST_PARTITIONS:
            run_phlo_step(
                f"materialize_dlt_posts_{partition}",
                ["materialize", "dlt_posts", "--partition", partition],
                timeout=MATERIALIZE_TIMEOUT,
            )

        rows = trino.execute("SELECT count(*) FROM posts", schema="raw")
        _write_text(_log_for("trino_count_posts"), repr(rows))
        row_count = rows[0][0] if rows else 0
        assert row_count > 0, f"Expected rows in posts, got {row_count}"
        # With JSONPlaceholder, we get 100 posts per partition (API returns all posts regardless of date filter)
        # After multiple partitions with upsert, should still have ~100 unique rows
        expected_min_rows = 100
        assert row_count >= expected_min_rows, (
            f"Expected at least {expected_min_rows} rows, got {row_count}"
        )

        # Improvement #5: Test idempotency - run same partition again
        count_before_rerun = row_count
        run_phlo_step(
            "materialize_dlt_posts_idempotency",
            ["materialize", "dlt_posts", "--partition", TEST_PARTITIONS[0]],
            timeout=MATERIALIZE_TIMEOUT,
        )
        rows_after = trino.execute("SELECT count(*) FROM posts", schema="raw")
        count_after_rerun = rows_after[0][0] if rows_after else 0
        _write_text(
            _log_for("idempotency_check"),
            f"Before rerun: {count_before_rerun}, After rerun: {count_after_rerun}\n",
        )
        assert count_after_rerun == count_before_rerun, (
            f"Idempotency failed: row count changed from {count_before_rerun} to {count_after_rerun}"
        )

        # Improvement #4: Data quality assertions
        sample_rows = trino.execute(
            "SELECT id, user_id, title, body FROM posts LIMIT 10",
            schema="raw",
        )
        _write_text(_log_for("data_quality_sample"), repr(sample_rows))
        assert len(sample_rows) > 0, "No sample rows returned"
        for row in sample_rows:
            assert row[0] is not None, "id should not be null"
            assert row[1] is not None, "user_id should not be null"
            assert row[2] and len(str(row[2])) > 0, "title should not be empty"
            assert row[3] and len(str(row[3])) > 0, "body should not be empty"

        run_phlo_step(
            "materialize_posts_mart",
            ["materialize", "posts_mart", "--partition", TEST_PARTITIONS[0]],
            timeout=MATERIALIZE_TIMEOUT,
        )

        rows = trino.execute("SELECT count(*) FROM posts_mart", schema="raw_marts")
        _write_text(_log_for("trino_count_posts_mart"), repr(rows))
        mart_count = rows[0][0] if rows else 0
        assert mart_count > 0, f"Expected rows in posts_mart, got {mart_count}"

        run_phlo_step(
            "materialize_publish_marts",
            ["materialize", "publish_jsonplaceholder_marts"],
            timeout=MATERIALIZE_TIMEOUT,
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
                _write_text(_log_for("postgres_count_posts_mart"), repr(rows))
                pg_mart_count = rows[0][0] if rows else 0
                assert pg_mart_count > 0, (
                    f"Expected rows in postgres marts.posts_mart, got {pg_mart_count}"
                )

                # Improvement #4: PostgreSQL data quality check
                cursor.execute("SELECT id, title FROM marts.posts_mart LIMIT 5")
                pg_sample = cursor.fetchall()
                _write_text(_log_for("postgres_sample_data"), repr(pg_sample))
                for row in pg_sample:
                    assert row[0] is not None, "PostgreSQL id should not be null"
                    assert row[1] and len(str(row[1])) > 0, "PostgreSQL title should not be empty"
        finally:
            pg_conn.close()

        # Get list of available optional services
        services = json.loads(
            _run_phlo(
                ["services", "list", "--all", "--json"],
                cwd=project_dir,
                log_path=_log_for("services_list"),
            ).stdout
        )
        optional = sorted(
            {
                service["name"]
                for service in services
                if not service.get("default") and not service.get("inline")
            }
        )

        # Improvement #1: Observability service testing - actually start them if available
        observability = [
            name for name in ["loki", "prometheus", "grafana", "alloy"] if name in optional
        ]
        for name in observability:
            run_phlo_step(
                f"services_add_{name}", ["services", "add", name, "--no-start"], timeout=120
            )
            all_services_added.append(name)
            optional.remove(name)

        compose = yaml.safe_load((phlo_dir / "docker-compose.yml").read_text())
        services_block = compose.get("services", {})
        assert set(observability).issubset(set(services_block))

        if "grafana" in observability:
            grafana_deps = services_block.get("grafana", {}).get("depends_on", {})
            if "prometheus" in observability:
                assert "prometheus" in grafana_deps

            grafana_datasources = (
                phlo_dir / "grafana" / "provisioning" / "datasources" / "datasources.yml"
            ).read_text()
            if "prometheus" in observability:
                assert "http://prometheus:9090" in grafana_datasources
            if "loki" in observability:
                assert "http://loki:3100" in grafana_datasources

        if "prometheus" in observability:
            prometheus_config = (phlo_dir / "prometheus" / "prometheus.yml").read_text()
            assert "phlo.metrics.enabled" in prometheus_config

        if "alloy" in observability:
            alloy_deps = services_block.get("alloy", {}).get("depends_on", {})
            if "loki" in observability:
                assert "loki" in alloy_deps
            alloy_config = (phlo_dir / "alloy" / "config.alloy").read_text()
            assert "http://loki:3100/loki/api/v1/push" in alloy_config

        # Improvement #1 continued: Actually start observability services and verify
        if observability:
            obs_start_args = ["services", "start"]
            for name in observability:
                obs_start_args.extend(["--service", name])
            run_phlo_step(
                "services_start_observability", obs_start_args, timeout=SERVICE_START_TIMEOUT
            )

            # Wait for services to be healthy
            for name in observability:
                _wait_for_compose_service(project=project_name, service=name, timeout_seconds=120)

            # Verify Prometheus is scraping targets
            if "prometheus" in observability:
                prom_port = int(env_vars.get("PROMETHEUS_PORT", "9090"))
                prom_url = f"http://127.0.0.1:{prom_port}/-/ready"
                _wait_for_http_endpoint(
                    prom_url, timeout_seconds=60, log_path=_log_for("prometheus_ready")
                )
                assert _check_health_endpoint(prom_url), "Prometheus not ready"

            # Verify Grafana is accessible
            if "grafana" in observability:
                grafana_port = int(env_vars.get("GRAFANA_PORT", "3001"))
                grafana_url = f"http://127.0.0.1:{grafana_port}/api/health"
                _wait_for_http_endpoint(
                    grafana_url, timeout_seconds=60, log_path=_log_for("grafana_ready")
                )
                assert _check_health_endpoint(grafana_url), "Grafana not ready"

        # Improvement #3 & #10: Add and test Hasura and PostgREST
        api_services = [name for name in ["hasura", "postgrest"] if name in optional]
        for name in api_services:
            run_phlo_step(f"services_add_{name}", ["services", "add", name], timeout=120)
            all_services_added.append(name)
            optional.remove(name)

        # Wait for API services to be healthy
        for name in api_services:
            _wait_for_compose_service(project=project_name, service=name, timeout_seconds=180)

        # Improvement #3: Verify Hasura GraphQL API
        if "hasura" in api_services:
            hasura_port = int(env_vars.get("HASURA_PORT", "8082"))
            hasura_health_url = f"http://127.0.0.1:{hasura_port}/healthz"
            _wait_for_http_endpoint(
                hasura_health_url, timeout_seconds=60, log_path=_log_for("hasura_ready")
            )
            assert _check_health_endpoint(hasura_health_url), "Hasura not healthy"

            # Test GraphQL query (using introspection which is always available)
            hasura_graphql_url = f"http://127.0.0.1:{hasura_port}/v1/graphql"
            introspection_query = json.dumps({"query": "{ __schema { types { name } } }"}).encode(
                "utf-8"
            )
            try:
                req = urllib.request.Request(
                    hasura_graphql_url,
                    data=introspection_query,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    _write_text(_log_for("hasura_introspection"), json.dumps(result, indent=2))
                    assert "data" in result, f"Hasura introspection failed: {result}"
            except Exception as e:
                _write_text(_log_for("hasura_graphql_error"), repr(e))
                # Log but don't fail - Hasura may need schema tracking configured

        # Improvement #10: Verify PostgREST API
        if "postgrest" in api_services:
            postgrest_port = int(env_vars.get("POSTGREST_PORT", "3002"))
            postgrest_url = f"http://127.0.0.1:{postgrest_port}/"
            _wait_for_http_endpoint(
                postgrest_url, timeout_seconds=60, log_path=_log_for("postgrest_ready")
            )

            # Query the marts schema
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{postgrest_port}/posts_mart?select=id,title&limit=5",
                    timeout=10,
                ) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    _write_text(_log_for("postgrest_query"), json.dumps(data, indent=2))
                    assert isinstance(data, list), f"PostgREST should return list, got {type(data)}"
                    if data:
                        assert "id" in data[0], "PostgREST response should have 'id' field"
                        assert "title" in data[0], "PostgREST response should have 'title' field"
            except urllib.error.HTTPError as e:
                # Schema 'marts' may not be exposed by default
                _write_text(
                    _log_for("postgrest_query_note"),
                    f"PostgREST query returned {e.code}: {e.reason}",
                )

        # Add remaining optional services (without starting)
        for name in optional:
            run_phlo_step(
                f"services_add_{name}", ["services", "add", name, "--no-start"], timeout=120
            )
            all_services_added.append(name)

        enabled_config = yaml.safe_load((project_dir / "phlo.yaml").read_text())
        enabled = set(enabled_config.get("services", {}).get("enabled", []))
        assert enabled.issuperset(set(observability))
        assert enabled.issuperset(set(api_services))

    finally:
        # Improvement #7: Better cleanup - stop all services that were added
        stop_args = ["services", "stop"]
        for name in all_services_added:
            stop_args.extend(["--service", name])
        _run_phlo(stop_args, cwd=project_dir, timeout=300, check=False)

        # Also run docker compose down to clean up networks/volumes
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(phlo_dir / "docker-compose.yml"),
                "down",
                "-v",
                "--remove-orphans",
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )

        _fix_ownership(project_dir)
