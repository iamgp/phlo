"""Logs command for viewing service logs."""

import sys
from subprocess import TimeoutExpired
from typing import Optional

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir, require_docker
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name


@click.command("logs")
@click.argument("service", required=False)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
@click.option("-n", "--tail", default=100, help="Number of lines to show")
def logs_cmd(service: Optional[str], follow: bool, tail: int):
    """View logs from Phlo infrastructure services.

    Examples:
        phlo services logs
        phlo services logs dagster
        phlo services logs -f
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["logs", "--tail", str(tail)])

    if follow:
        cmd.append("-f")

    if service:
        cmd.append(service)

    try:
        run_command(cmd, check=False, capture_output=False)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker logs timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
