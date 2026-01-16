"""Status command for showing service status."""

import sys
from subprocess import TimeoutExpired

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir, require_docker
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name


@click.command("status")
def status_cmd():
    """Show status of Phlo infrastructure services.

    Examples:
        phlo services status
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"])

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo("No services running or error checking status.", err=True)
            sys.exit(result.returncode or 1)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
