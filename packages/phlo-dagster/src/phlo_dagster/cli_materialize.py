"""Materialize Dagster assets via Docker."""

from __future__ import annotations

import platform
import subprocess
import sys
from typing import Optional

import click

from phlo.cli.services import find_dagster_container, get_project_name


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
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            click.echo(f"\nSuccessfully materialized {asset_name}")
        else:
            click.echo(
                f"\nMaterialization failed with exit code {result.returncode}",
                err=True,
            )
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo(
            f"Error: Docker not found or {container_name} container not running",
            err=True,
        )
        click.echo("\nStart services with: phlo services start", err=True)
        sys.exit(1)
