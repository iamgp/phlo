"""Remove command for removing services from the project."""

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
from phlo.plugins.discovery import ServiceDiscovery


@click.command("remove")
@click.argument("service_name")
@click.option("--keep-running", is_flag=True, help="Don't stop the service")
def remove_cmd(service_name: str, keep_running: bool):
    """Remove a service from the project.

    This removes the service from your configuration.

    Examples:
        phlo services remove prometheus
        phlo services remove grafana --keep-running
    """
    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        sys.exit(1)

    # Load project config
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
    else:
        click.echo("Error: phlo.yaml not found.", err=True)
        sys.exit(1)

    # Discover available services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if service_name not in all_services:
        click.echo(f"Error: Service '{service_name}' not found.", err=True)
        sys.exit(1)

    service = all_services[service_name]

    # Stop the service first if running
    if not keep_running:
        project_name = get_project_name()

        click.echo(f"Stopping {service_name}...")

        try:
            cmd = compose_base_cmd(
                phlo_dir=phlo_dir,
                project_name=project_name,
                profiles=() if not service.profile else (service.profile,),
            )
            cmd.extend(["stop", service_name])
            run_command(cmd, check=False, capture_output=False)
        except (FileNotFoundError, TimeoutExpired, OSError):
            click.echo(f"Warning: Could not stop {service_name}.", err=True)

    # Update config
    if not isinstance(config.get("services"), dict):
        config["services"] = {}
    if "disabled" not in config["services"]:
        config["services"]["disabled"] = []
    if "enabled" not in config["services"]:
        config["services"]["enabled"] = []

    # Remove from enabled if present
    enabled = config["services"]["enabled"]
    if service_name in enabled:
        enabled.remove(service_name)

    # Add to disabled
    disabled = config["services"]["disabled"]
    if service_name not in disabled:
        disabled.append(service_name)
        config["services"]["disabled"] = sorted(set(disabled))

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Removed '{service_name}' from phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)

    click.echo(f"Service '{service_name}' removed.")
