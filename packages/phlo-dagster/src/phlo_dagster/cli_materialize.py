"""Materialize Dagster assets via Docker."""

from __future__ import annotations

import platform
import subprocess
import sys
import time
from typing import Optional

import click

from phlo.cli.infrastructure.utils import get_project_name
from phlo_dagster.containers import find_dagster_container
from phlo.logging import get_logger


@click.command()
@click.argument("asset_name")
@click.option("-p", "--partition", help="Partition date (YYYY-MM-DD)")
@click.option("--select", help="Asset selector expression")
@click.option("--dry-run", is_flag=True, help="Show command without executing")
def materialize(
    asset_name: str,
    partition: Optional[str],
    select: Optional[str],
    dry_run: bool,
) -> None:
    """
    Materialize Dagster assets via Docker.

    Examples:
        phlo materialize dlt_glucose_entries
        phlo materialize dlt_glucose_entries --partition 2025-01-15
        phlo materialize --select "tag:nightscout"
        phlo materialize dlt_glucose_entries --dry-run
    """
    logger = get_logger("phlo.dagster.materialize", service="dagster")
    started_at = time.perf_counter()
    project_name = get_project_name()
    container_name = "dagster"
    logger.info(
        "dagster_materialize_command_started",
        asset_name=asset_name,
        partition=partition,
        select=select,
        dry_run=dry_run,
        project_name=project_name,
    )

    try:
        container_name = find_dagster_container(project_name)
        host_platform = platform.system()

        cmd = [
            "docker",
            "exec",
            "-e",
            f"PHLO_HOST_PLATFORM={host_platform}",
            "-e",
            "PHLO_PROJECT_PATH=/app",
            "-w",
            "/app",
            container_name,
            "dagster",
            "asset",
            "materialize",
            "-m",
            "phlo_dagster.framework.definitions",
        ]

        if select:
            cmd.extend(["--select", select])
        else:
            cmd.extend(["--select", asset_name])

        if partition:
            cmd.extend(["--partition", partition])

        if dry_run:
            click.echo("Dry run - would execute:\n")
            click.echo(" ".join(cmd))
            logger.info(
                "dagster_materialize_command_completed",
                asset_name=asset_name,
                partition=partition,
                select=select,
                dry_run=True,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=0,
            )
            sys.exit(0)

        click.echo(f"Materializing {asset_name}...\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if process.stdout:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                message = line.rstrip()
                if message:
                    logger.info(message, tags={"source": "dagster"})
        returncode = process.wait()
        if returncode == 0:
            click.echo(f"\nSuccessfully materialized {asset_name}")
            logger.info(
                "dagster_materialize_command_completed",
                asset_name=asset_name,
                partition=partition,
                select=select,
                dry_run=False,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=returncode,
            )
        else:
            click.echo(
                f"\nMaterialization failed with exit code {returncode}",
                err=True,
            )
            logger.error(
                "dagster_materialize_command_failed",
                asset_name=asset_name,
                partition=partition,
                select=select,
                dry_run=False,
                project_name=project_name,
                container_name=container_name,
                duration_seconds=round(time.perf_counter() - started_at, 3),
                returncode=returncode,
            )
        sys.exit(returncode)
    except FileNotFoundError:
        logger.error(
            "dagster_materialize_command_failed",
            asset_name=asset_name,
            partition=partition,
            select=select,
            dry_run=dry_run,
            project_name=project_name,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            error="docker_not_found_or_container_not_running",
            exc_info=True,
        )
        click.echo(
            f"Error: Docker not found or {container_name} container not running",
            err=True,
        )
        click.echo("\nStart services with: phlo services start", err=True)
        sys.exit(1)
    except Exception as exc:
        logger.error(
            "dagster_materialize_command_failed",
            asset_name=asset_name,
            partition=partition,
            select=select,
            dry_run=dry_run,
            project_name=project_name,
            duration_seconds=round(time.perf_counter() - started_at, 3),
            error=str(exc),
            exc_info=True,
        )
        raise
