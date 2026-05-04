"""Materialize command for Dagster assets via Docker.

This module implements the `phlo materialize` CLI command, providing a
convenient interface for materializing Dagster assets through Docker
container execution. It handles environment setup and passes through
to Dagster's asset materialization CLI.

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

Docker Integration:
    The command uses `docker exec` to run Dagster CLI commands within
the running Dagster container. This ensures:
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

import platform
import subprocess
import sys
import time
from collections import deque
from typing import Optional

import click

from phlo.cli.infrastructure.utils import get_project_name
from phlo.cli.output import command_failed_error, service_unavailable_error
from phlo_dagster.containers import find_dagster_container
from phlo.logging import get_logger


def _summarize_process_output(lines: list[str]) -> str | None:
    """Return a short human-readable failure hint from process output."""
    for line in reversed(lines):
        message = line.strip()
        if message and not message.startswith("{"):
            return message[:240]
    return None


def wait_for_dagster_runtime(container_name: str, timeout_seconds: float = 600.0) -> None:
    """Wait until the Dagster container has finished entrypoint setup."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "sh",
                "-lc",
                "test -f /tmp/phlo-dagster-ready "
                "|| python -c 'import phlo_dagster.framework.definitions'",
            ],
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


@click.command(help="Materialize Dagster assets via Docker.")
@click.argument("asset_name", required=False)
@click.option("-p", "--partition", help="Partition date (YYYY-MM-DD)")
@click.option("--select", help="Asset selector expression")
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
    no_contract_refresh: bool,
    dry_run: bool,
) -> None:
    """Materialize Dagster assets via Docker.

    Args:
        asset_name: Name of the asset to materialize.
        partition: Optional partition date (YYYY-MM-DD) for partitioned assets.
        select: Optional asset selector expression to override asset_name.
        no_contract_refresh: If True, skip automatic schema contract refresh.
        dry_run: If True, show command without executing.

    Returns:
        None

    Raises:
        SystemExit: On command failure or Docker not found.

    """
    if not asset_name and not select:
        raise click.UsageError("Provide ASSET_NAME or --select.")
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

        if not dry_run:
            container_name = find_dagster_container(project_name)
            wait_for_dagster_runtime(container_name)

        cmd = [
            "docker",
            "exec",
            "-e",
            f"PHLO_HOST_PLATFORM={host_platform}",
            "-e",
            "PHLO_PROJECT_PATH=/app",
            "-e",
            f"PHLO_AUTO_REFRESH_CONTRACTS={'0' if no_contract_refresh else '1'}",
            "-e",
            f"PHLO_CONTRACT_REFRESH_SELECTION={effective_selection}",
            "-w",
            "/app",
            container_name,
            "dagster",
            "asset",
            "materialize",
            "-m",
            "phlo_dagster.framework.definitions",
        ]

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
