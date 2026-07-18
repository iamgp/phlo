"""Materialize command for Dagster assets via the configured container backend.

This module implements the `phlo materialize` CLI command, providing a
convenient interface for materializing Dagster assets through Docker or
Podman container execution. It handles environment setup and passes
through to Dagster's asset materialization CLI.

Features:
    - Single asset or asset selection expression materialization
    - Partition support for time-sliced assets
    - Schema contract refresh control
    - Dry-run mode for command preview
    - Platform-aware environment injection (PHLO_HOST_PLATFORM)
    - Automatic Dagster container discovery
    - Streaming output from container execution

Environment Variables:
    - PHLO_HOST_PLATFORM: Host OS platform for DuckDB compatibility
    - PHLO_PROJECT_PATH: Project path within container
    - PHLO_AUTO_REFRESH_CONTRACTS: Enable schema contract refresh
    - PHLO_CONTRACT_REFRESH_SELECTION: Assets to refresh contracts for

Container Integration:
    The command uses the selected project container backend to run Dagster
CLI commands within the running Dagster container. This ensures:
    - Access to configured resources (Trino, MinIO, etc.)
    - Consistent Python environment
    - Proper logging context

Example:
    CLI usage::

        phlo materialize dlt_orders
        phlo materialize dlt_orders --partition 2025-01-15
        phlo materialize --select "tag:bronze"
        phlo materialize dlt_orders --dry-run
        phlo materialize dlt_orders --no-contract-refresh

"""

from __future__ import annotations

import asyncio
import os
import platform
import subprocess
import sys
import time
import uuid
from collections import deque
from typing import Optional

import click

from phlo.cli.infrastructure.container_backend import (
    ContainerBackend,
    select_project_container_backend,
)
from phlo.cli.infrastructure.utils import get_project_name
from phlo.cli.output import command_failed_error, service_unavailable_error
from phlo_dagster.containers import find_dagster_container
from phlo_dagster.operations import launch_materialize
from phlo_dagster.wap_launch import prepare_wap_launch
from phlo.logging import get_logger


def _summarize_process_output(lines: list[str]) -> str | None:
    """Return a short human-readable failure hint from process output."""
    for line in reversed(lines):
        message = line.strip()
        if message and not message.startswith("{"):
            return message[:240]
    return None


def wait_for_dagster_runtime(
    container_name: str,
    timeout_seconds: float = 600.0,
    backend: ContainerBackend | None = None,
) -> None:
    """Wait until the Dagster container has finished entrypoint setup."""
    selected_backend = backend or select_project_container_backend()
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            selected_backend.container_exec_cmd(
                container_name=container_name,
                command=[
                    "sh",
                    "-lc",
                    "test -f /tmp/phlo-dagster-ready "
                    "|| python -c 'import phlo_dagster.framework.definitions'",
                ],
            ),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)

    raise RuntimeError(
        "Dagster container is still finishing runtime setup. "
        "Inspect startup logs with: phlo services logs --tail 120 dagster"
    )


@click.command(help="Materialize Dagster assets via the configured container backend.")
@click.argument("asset_name", required=False)
@click.option("-p", "--partition", help="Partition date (YYYY-MM-DD)")
@click.option("--select", help="Asset selector expression")
@click.option("--wap", is_flag=True, help="Launch one asset through the WAP branch lifecycle")
@click.option("--wap-run-id", help="Reuse this logical run identity for a WAP retry")
@click.option("--job-name", help="Dagster job name required for a WAP launch")
@click.option(
    "--repository-location-name",
    envvar="PHLO_DAGSTER_REPOSITORY_LOCATION_NAME",
    help="Dagster repository location for a WAP launch",
)
@click.option(
    "--repository-name",
    envvar="PHLO_DAGSTER_REPOSITORY_NAME",
    help="Dagster repository name for a WAP launch",
)
@click.option(
    "--dagster-url",
    envvar="DAGSTER_GRAPHQL_URL",
    default="http://localhost:3000/graphql",
    show_default=True,
    help="Dagster GraphQL endpoint for a WAP launch",
)
@click.option(
    "--no-contract-refresh",
    is_flag=True,
    help="Skip automatic schema contract refresh before materialization",
)
@click.option("--dry-run", is_flag=True, help="Show command without executing")
def materialize(
    asset_name: str | None,
    partition: Optional[str],
    select: Optional[str],
    wap: bool,
    wap_run_id: str | None,
    job_name: str | None,
    repository_location_name: str | None,
    repository_name: str | None,
    dagster_url: str,
    no_contract_refresh: bool,
    dry_run: bool,
) -> None:
    """Materialize Dagster assets via the configured container backend.

    Args:
        asset_name: Name of the asset to materialize.
        partition: Optional partition date (YYYY-MM-DD) for partitioned assets.
        select: Optional asset selector expression to override asset_name.
        no_contract_refresh: If True, skip automatic schema contract refresh.
        dry_run: If True, show command without executing.

    Returns:
        None

    Raises:
        SystemExit: On command failure or container backend not found.

    """
    if not asset_name and not select:
        raise click.UsageError("Provide ASSET_NAME or --select.")
    if wap:
        if not asset_name or select:
            raise click.UsageError(
                "WAP materialization requires one ASSET_NAME and does not support --select."
            )
        if not job_name:
            raise click.UsageError("WAP materialization requires --job-name.")
        if not repository_location_name or not repository_name:
            raise click.UsageError(
                "WAP materialization requires --repository-location-name and --repository-name "
                "(or PHLO_DAGSTER_REPOSITORY_LOCATION_NAME and PHLO_DAGSTER_REPOSITORY_NAME)."
            )
        access_token = os.environ.get("PHLO_DAGSTER_ACCESS_TOKEN")
        if not access_token:
            raise click.UsageError("WAP materialization requires PHLO_DAGSTER_ACCESS_TOKEN.")

        logical_run_id = wap_run_id or uuid.uuid4().hex
        if dry_run:
            click.echo(
                "WAP dry run - would launch "
                f"{asset_name} with logical run ID {logical_run_id} through {dagster_url}"
            )
            return

        wap_launch = prepare_wap_launch(logical_run_id=logical_run_id)
        try:
            result = asyncio.run(
                launch_materialize(
                    dagster_url=dagster_url,
                    asset_key_path=asset_name,
                    job_name=job_name,
                    repository_location_name=repository_location_name,
                    repository_name=repository_name,
                    access_token=access_token,
                    partition_key=partition,
                    idempotency_key=logical_run_id,
                    tags=wap_launch.tags,
                )
            )
        except Exception:
            # A timeout or transport failure can occur after Dagster accepts the
            # mutation. Retain a branch we created so the run can be reconciled
            # or retried with the same logical run ID.
            raise

        if not result.accepted:
            wap_launch.cleanup_if_created()
            raise click.ClickException(result.message)

        click.echo(
            f"Launched WAP materialization for {asset_name} on {wap_launch.branch} "
            f"(logical run {logical_run_id}, Dagster run {result.run_id})"
        )
        return
    effective_selection = select or asset_name or ""

    logger = get_logger("phlo.dagster.materialize", service="dagster")
    started_at = time.perf_counter()
    project_name = get_project_name()
    container_name = "dagster"
    logger.info(
        "dagster_materialize_command_started",
        asset_name=effective_selection,
        partition=partition,
        select=select,
        no_contract_refresh=no_contract_refresh,
        dry_run=dry_run,
        project_name=project_name,
    )

    try:
        host_platform = platform.system()
        backend = select_project_container_backend()

        if not dry_run:
            container_name = find_dagster_container(project_name)
            wait_for_dagster_runtime(container_name, backend=backend)

        cmd = backend.container_exec_cmd(
            container_name=container_name,
            env={
                "PHLO_HOST_PLATFORM": host_platform,
                "PHLO_PROJECT_PATH": "/app",
                "PHLO_AUTO_REFRESH_CONTRACTS": "0" if no_contract_refresh else "1",
                "PHLO_CONTRACT_REFRESH_SELECTION": effective_selection,
            },
            workdir="/app",
            command=[
                "dagster",
                "asset",
                "materialize",
                "-m",
                "phlo_dagster.framework.definitions",
            ],
        )

        cmd.extend(["--select", effective_selection])

        if partition:
            cmd.extend(["--partition", partition])

        if dry_run:
            click.echo("Dry run - would execute:\n")
            click.echo(" ".join(cmd))
            logger.info(
                "dagster_materialize_command_completed",
                asset_name=effective_selection,
                partition=partition,
                select=select,
                no_contract_refresh=no_contract_refresh,
                dry_run=True,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=0,
            )
            sys.exit(0)

        click.echo(f"Materializing {effective_selection}...\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        recent_output: deque[str] = deque(maxlen=20)
        if process.stdout:
            for line in process.stdout:
                message = line.rstrip()
                if message:
                    recent_output.append(message)
                    logger.debug(
                        "dagster_materialize_process_output",
                        source="dagster",
                        line=message,
                    )
        returncode = process.wait()
        if returncode == 0:
            click.echo(f"\nSuccessfully materialized {effective_selection}")
            logger.info(
                "dagster_materialize_command_completed",
                asset_name=effective_selection,
                partition=partition,
                select=select,
                no_contract_refresh=no_contract_refresh,
                dry_run=False,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=returncode,
            )
        else:
            output_hint = _summarize_process_output(list(recent_output))
            logger.error(
                "dagster_materialize_command_failed",
                asset_name=effective_selection,
                partition=partition,
                select=select,
                no_contract_refresh=no_contract_refresh,
                dry_run=False,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=returncode,
            )
            raise command_failed_error(
                "materialization",
                exit_code=returncode,
                details=[f"Last output: {output_hint}"] if output_hint else None,
                run="phlo logs --level ERROR --limit 20",
            )
    except FileNotFoundError:
        logger.error(
            "dagster_materialize_command_failed",
            asset_name=effective_selection,
            partition=partition,
            select=select,
            no_contract_refresh=no_contract_refresh,
            dry_run=dry_run,
            project_name=project_name,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            error="docker_not_found_or_container_not_running",
            exc_info=True,
        )
        raise service_unavailable_error(container_name) from None
    except RuntimeError as exc:
        logger.error(
            "dagster_materialize_service_unavailable",
            asset_name=effective_selection,
            partition=partition,
            select=select,
            no_contract_refresh=no_contract_refresh,
            dry_run=dry_run,
            project_name=project_name,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            error=str(exc),
            exc_info=True,
        )
        raise service_unavailable_error("dagster") from exc
    except click.ClickException:
        raise
    except Exception as exc:
        logger.error(
            "dagster_materialize_command_failed",
            asset_name=effective_selection,
            partition=partition,
            select=select,
            no_contract_refresh=no_contract_refresh,
            dry_run=dry_run,
            project_name=project_name,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            error=str(exc),
            exc_info=True,
        )
        raise
