"""Add command for adding services to the project."""

import sys
from pathlib import Path
from subprocess import TimeoutExpired

import click
import yaml

from phlo.cli.commands.services.utils import (
    PHLO_CONFIG_FILE,
    _regenerate_compose,
    get_phlo_dir,
)
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.discovery import ServiceDiscovery


@click.command("add")
@click.argument("service_name")
@click.option("--no-start", is_flag=True, help="Don't start the service after adding")
def add_cmd(service_name: str, no_start: bool):
    """Add an optional service to the project.

    Examples:
        phlo services add prometheus
        phlo services add grafana --no-start
        phlo services add hasura
    """
    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Load project config
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config, dict):
            click.echo("Error: phlo.yaml must contain a mapping.", err=True)
            sys.exit(1)
    else:
        click.echo("Error: phlo.yaml not found.", err=True)
        sys.exit(1)

    # Discover available services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if service_name not in all_services:
        click.echo(f"Error: Service '{service_name}' not found.", err=True)
        click.echo("")
        click.echo("Available services:")
        for name in sorted(all_services.keys()):
            svc = all_services[name]
            marker = "[optional]" if svc.profile or not svc.default else "[default]"
            click.echo(f"  {name} {marker}")
        sys.exit(1)

    service = all_services[service_name]

    # Update config
    if "services" not in config:
        config["services"] = {}
    if "enabled" not in config["services"]:
        config["services"]["enabled"] = []

    enabled = config["services"]["enabled"]
    if service_name in enabled:
        click.echo(f"Service '{service_name}' is already enabled.")
        return

    enabled.append(service_name)
    config["services"]["enabled"] = sorted(set(enabled))

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Added '{service_name}' to phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)

    click.echo(f"Service '{service_name}' added.")

    if not no_start:
        click.echo("")
        click.echo(f"Starting {service_name}...")
        project_name = get_project_name()

        cmd = compose_base_cmd(
            phlo_dir=phlo_dir,
            project_name=project_name,
            profiles=() if not service.profile else (service.profile,),
        )
        cmd.extend(["up", "-d", service_name])
        try:
            result = run_command(cmd, check=False, capture_output=False)
            if result.returncode == 0:
                click.echo(f"Service '{service_name}' started.")
            else:
                click.echo(f"Warning: Could not start {service_name}.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
        except (FileNotFoundError, TimeoutExpired, OSError) as e:
            click.echo(f"Warning: Could not start {service_name}: {e}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
