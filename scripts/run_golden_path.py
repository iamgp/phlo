#!/usr/bin/env python3
"""
Golden Path E2E Workflow Script

Run the complete Phlo workflow end-to-end with live output.
This is the script version of test_golden_path_e2e.py for easier debugging.

Usage:
    python scripts/run_golden_path.py [--mode dev|pypi] [--keep-running]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path

# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(msg: str, color: str = "") -> None:
    """Print a log message with optional color."""
    print(f"{color}{msg}{RESET}")


def log_step(step: str) -> None:
    """Print a step header."""
    print()
    log(f"{'=' * 60}", BLUE)
    log(f"  {step}", BOLD + BLUE)
    log(f"{'=' * 60}", BLUE)


def log_success(msg: str) -> None:
    log(f"[OK] {msg}", GREEN)


def log_error(msg: str) -> None:
    log(f"[FAIL] {msg}", RED)


def log_warning(msg: str) -> None:
    log(f"[WARN]  {msg}", YELLOW)


def log_info(msg: str) -> None:
    log(f"[INFO]  {msg}", BLUE)


def run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
    check: bool = True,
    stream_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command with live output streaming."""
    log_info(f"Running: {' '.join(args)}")

    if stream_output:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines = []
        try:
            for line in process.stdout:
                print(f"    {line}", end="")
                output_lines.append(line)
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            raise

        result = subprocess.CompletedProcess(
            args=args,
            returncode=process.returncode,
            stdout="".join(output_lines),
            stderr="",
        )
    else:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

    if check and result.returncode != 0:
        log_error(f"Command failed with exit code {result.returncode}")
        if result.stderr:
            print(result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(args)}")

    return result


def run_phlo(
    args: list[str],
    *,
    cwd: Path,
    timeout: int | None = None,
    check: bool = True,
    stream_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a phlo CLI command."""
    return run_command(
        [sys.executable, "-m", "phlo.cli.main", *args],
        cwd=cwd,
        timeout=timeout,
        check=check,
        stream_output=stream_output,
    )


def wait_for_http(url: str, *, timeout: int = 60, name: str = "endpoint") -> bool:
    """Wait for an HTTP endpoint to become available."""
    log_info(f"Waiting for {name} at {url}...")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    log_success(f"{name} is ready")
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(2)
        print(".", end="", flush=True)
    print()
    log_warning(f"{name} not ready after {timeout}s")
    return False


def read_env_file(path: Path) -> dict[str, str]:
    """Read a .env file into a dict."""
    data: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def write_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    log_info(f"Created: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Golden Path E2E Workflow")
    parser.add_argument(
        "--mode", choices=["dev", "pypi"], default="dev", help="Installation mode (default: dev)"
    )
    parser.add_argument(
        "--keep-running", action="store_true", help="Keep services running after test"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Project directory (default: /tmp/phlo-golden-path)",
    )
    args = parser.parse_args()

    project_name = "phlo-golden-path"
    project_dir = args.project_dir or Path("/tmp") / project_name
    phlo_source = Path(__file__).resolve().parents[1]

    log_step("Golden Path E2E Workflow")
    log_info(f"Mode: {args.mode}")
    log_info(f"Project dir: {project_dir}")
    log_info(f"Phlo source: {phlo_source}")

    # Clean up if exists
    if project_dir.exists():
        log_warning(f"Removing existing project dir: {project_dir}")
        shutil.rmtree(project_dir, ignore_errors=True)

    try:
        # Step 1: Initialize project
        log_step("Step 1: Initialize Project")
        run_phlo(
            ["init", project_name, "--template", "basic"],
            cwd=project_dir.parent,
            timeout=120,
        )
        log_success("Project initialized")

        # Step 2: Services init
        log_step("Step 2: Initialize Services")
        if args.mode == "dev":
            run_phlo(
                ["services", "init", "--dev", "--phlo-source", str(phlo_source), "--force"],
                cwd=project_dir,
                timeout=180,
            )
        else:
            run_phlo(
                ["services", "init", "--no-dev", "--force"],
                cwd=project_dir,
                timeout=180,
            )
        log_success("Services initialized")

        phlo_dir = project_dir / ".phlo"

        # Set API port to avoid conflicts
        with (phlo_dir / ".env").open("a") as f:
            f.write("\nPHLO_API_PORT=54000\n")
        log_info("Set PHLO_API_PORT=54000 to avoid conflicts")

        # Step 3: Create workflow
        log_step("Step 3: Create Workflow")
        run_phlo(
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
            cwd=project_dir,
            timeout=60,
        )
        log_success("Workflow created")

        # Update the asset with validate=False
        asset_file = project_dir / "workflows" / "ingestion" / "jsonplaceholder" / "posts.py"
        asset_content = textwrap.dedent('''
            """Jsonplaceholder posts ingestion asset."""

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
                base_url = "https://jsonplaceholder.typicode.com"
                return rest_api(
                    client={"base_url": base_url},
                    resources=[{"name": "posts", "endpoint": {"path": "posts"}}],
                )
        ''').lstrip()
        write_file(asset_file, asset_content)

        # Create dbt profiles and mart model
        write_file(
            project_dir / "transforms" / "dbt" / "profiles" / "profiles.yml",
            textwrap.dedent("""
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
            """).lstrip(),
        )

        write_file(
            project_dir / "transforms" / "dbt" / "models" / "marts" / "posts_mart.sql",
            textwrap.dedent("""
                {{ config(materialized='table', schema='marts') }}
                select cast(id as varchar) as id, user_id, title, body
                from iceberg.raw.posts
            """).lstrip(),
        )

        write_file(
            project_dir / "workflows" / "publishing" / "__init__.py",
            '"""Publishing assets."""\n',
        )

        write_file(
            project_dir / "workflows" / "publishing" / "jsonplaceholder.py",
            textwrap.dedent("""
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
            """).lstrip(),
        )

        # Step 4: Start core services
        log_step("Step 4: Start Core Services")
        core_services = ["postgres", "minio", "minio-setup", "nessie", "trino", "dagster"]
        start_args = ["services", "start"]
        for svc in core_services:
            start_args.extend(["--service", svc])
        run_phlo(start_args, cwd=project_dir, timeout=600)
        log_success("Core services started")

        # Wait for services to be healthy
        env_vars = read_env_file(phlo_dir / ".env")
        dagster_port = int(env_vars.get("DAGSTER_PORT", "3000"))
        trino_port = int(env_vars.get("TRINO_PORT", "8080"))
        postgres_port = int(env_vars.get("POSTGRES_PORT", "5432"))
        minio_port = int(env_vars.get("MINIO_API_PORT", "9000"))

        wait_for_http(f"http://127.0.0.1:{dagster_port}/server_info", name="Dagster", timeout=120)
        wait_for_http(f"http://127.0.0.1:{minio_port}/minio/health/live", name="MinIO", timeout=60)
        wait_for_http(f"http://127.0.0.1:{trino_port}/v1/info", name="Trino", timeout=120)

        # Step 5: Run DLT ingestion
        log_step("Step 5: Run DLT Ingestion")
        run_phlo(
            ["materialize", "dlt_posts", "--partition", "2025-01-01"],
            cwd=project_dir,
            timeout=1200,
        )
        log_success("DLT ingestion completed")

        # Step 6: Verify Trino data
        log_step("Step 6: Verify Trino Data")
        from phlo_trino import TrinoResource

        trino = TrinoResource(host="127.0.0.1", port=trino_port, catalog="iceberg")
        rows = trino.execute("SELECT count(*) FROM posts", schema="raw")
        count = rows[0][0] if rows else 0
        log_info(f"Row count in raw.posts: {count}")
        if count > 0:
            log_success(f"Data verified: {count} rows in Trino")
        else:
            log_error("No data in Trino!")
            return 1

        # Step 7: Run dbt transform
        log_step("Step 7: Run dbt Transform")
        run_phlo(
            ["materialize", "posts_mart", "--partition", "2025-01-01"],
            cwd=project_dir,
            timeout=1200,
        )
        log_success("dbt transform completed")

        # Verify mart
        rows = trino.execute("SELECT count(*) FROM posts_mart", schema="raw_marts")
        mart_count = rows[0][0] if rows else 0
        log_info(f"Row count in raw_marts.posts_mart: {mart_count}")

        # Step 8: Publish to PostgreSQL
        log_step("Step 8: Publish to PostgreSQL")
        run_phlo(
            ["materialize", "publish_jsonplaceholder_marts"],
            cwd=project_dir,
            timeout=1200,
        )
        log_success("Published to PostgreSQL")

        # Step 9: Verify PostgreSQL
        log_step("Step 9: Verify PostgreSQL Data")
        import psycopg2

        pg_conn = psycopg2.connect(
            host="localhost",
            port=postgres_port,
            user=env_vars.get("POSTGRES_USER", "phlo"),
            password=env_vars.get("POSTGRES_PASSWORD", "phlo"),
            dbname=env_vars.get("POSTGRES_DB", "phlo"),
        )
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM marts.posts_mart")
                pg_count = cursor.fetchone()[0]
                log_info(f"Row count in PostgreSQL marts.posts_mart: {pg_count}")
                if pg_count > 0:
                    log_success(f"PostgreSQL verified: {pg_count} rows")
                else:
                    log_error("No data in PostgreSQL!")
                    return 1
        finally:
            pg_conn.close()

        # Step 10: Add optional services
        log_step("Step 10: Add Optional Services")
        for svc in ["hasura", "postgrest"]:
            log_info(f"Adding {svc}...")
            run_phlo(["services", "add", svc], cwd=project_dir, timeout=120, check=False)

        log_step("=== Golden Path Complete!")
        log_success("All steps completed successfully!")
        log_info(f"Project directory: {project_dir}")
        log_info(f"Dagster UI: http://localhost:{dagster_port}")
        log_info(
            f"MinIO Console: http://localhost:{int(env_vars.get('MINIO_CONSOLE_PORT', '9001'))}"
        )

        if args.keep_running:
            log_info("Services are still running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

        return 0

    except Exception as e:
        log_error(f"Failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        if not args.keep_running:
            log_step("Cleanup")
            try:
                run_phlo(["services", "stop"], cwd=project_dir, timeout=300, check=False)
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(project_dir / ".phlo" / "docker-compose.yml"),
                        "down",
                        "-v",
                        "--remove-orphans",
                    ],
                    cwd=project_dir,
                    capture_output=True,
                    timeout=120,
                    check=False,
                )
                log_success("Cleanup complete")
            except Exception as e:
                log_warning(f"Cleanup error: {e}")


if __name__ == "__main__":
    sys.exit(main())
