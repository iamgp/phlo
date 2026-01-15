"""Restart command for restarting services."""

import sys
from subprocess import TimeoutExpired

import click

from phlo.cli.commands.services.utils import (
    ensure_phlo_dir,
    get_profile_service_names,
    require_docker,
)
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name


@click.command("restart")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option(
    "--profile",
    multiple=True,
    help="Restart optional profile services (e.g., observability, api)",
)
@click.option(
    "--service",
    multiple=True,
    help="Restart only specific service(s) (e.g., --service postgres,minio)",
)
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
def restart_cmd(
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    dev: bool,
):
    """Restart Phlo infrastructure services (stop + start).

    Combines stop and start in a single command for convenience.

    Examples:
        phlo services restart                          # Restart all services
        phlo services restart --profile observability  # Restart profile services only
        phlo services restart --service postgres       # Restart specific service
        phlo services restart --build                  # Rebuild before starting
    """
    require_docker()
    if dev:
        raise click.UsageError("dev mode not implemented for restart")

    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)
        if not services_list:
            profile_list = ", ".join(profile)
            raise click.UsageError(f"profile(s) resolve to no services: {profile_list}")

    if services_list:
        click.echo(f"Restarting services: {', '.join(services_list)}...")
    else:
        click.echo(f"Restarting {project_name} infrastructure...")

    # Stop services
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    if services_list:
        cmd.extend(["stop", *services_list])
    else:
        cmd.append("down")

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo(f"Warning: stop failed with code {result.returncode}", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Warning: stop timed out.", err=True)

    # Start services
    click.echo("")
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    cmd.extend(["up", "-d"])

    if build:
        cmd.append("--build")

    if services_list:
        cmd.extend(services_list)

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            click.echo("")
            if services_list:
                click.echo(f"Restarted services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure restarted.")
        else:
            click.echo(f"Error: start failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
