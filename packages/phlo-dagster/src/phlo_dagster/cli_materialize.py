"""Materialize Dagster assets via Docker."""

from __future__ import annotations

import platform
import subprocess
import sys
from typing import Optional

import click

from phlo.cli._services.utils import find_dagster_container, get_project_name
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
    project_name = get_project_name()
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
        "phlo.framework.definitions",
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
        sys.exit(0)

    click.echo(f"Materializing {asset_name}...\n")

    try:
        logger = get_logger("phlo.dagster.materialize", service="dagster")
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
        else:
            click.echo(
                f"\nMaterialization failed with exit code {returncode}",
                err=True,
            )
        sys.exit(returncode)
    except FileNotFoundError:
        click.echo(
            f"Error: Docker not found or {container_name} container not running",
            err=True,
        )
        click.echo("\nStart services with: phlo services start", err=True)
        sys.exit(1)
