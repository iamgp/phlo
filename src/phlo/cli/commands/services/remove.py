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
    normalize_services_enabled_disabled_config,
)
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger
from phlo.plugins.discovery import ServiceDiscovery

logger = get_logger(__name__)


def _dependent_closure(
    all_services: dict[str, object],
    service_name: str,
) -> list[str]:
    """Return services that directly or transitively depend on a service."""
    dependents: list[str] = []
    queue = [service_name]
    seen = {service_name}
    while queue:
        current = queue.pop(0)
        for candidate_name, candidate in all_services.items():
            depends_on = getattr(candidate, "depends_on", [])
            if current not in depends_on or candidate_name in seen:
                continue
            seen.add(candidate_name)
            dependents.append(candidate_name)
            queue.append(candidate_name)
    return dependents


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
    logger.info(
        "services_remove_requested",
        service_name=service_name,
        keep_running=keep_running,
    )

    if not phlo_dir.exists():
        logger.error("services_remove_missing_phlo_dir", phlo_dir=str(phlo_dir))
        click.echo("Error: .phlo directory not found.", err=True)
        sys.exit(1)

    # Load project config
    if config_file.exists():
        with config_file.open() as f:
            config = yaml.safe_load(f) or {}
    else:
        logger.error("services_remove_missing_config", config_file=str(config_file))
        click.echo("Error: phlo.yaml not found.", err=True)
        sys.exit(1)

    # Discover available services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if service_name not in all_services:
        logger.warning(
            "services_remove_unknown_service",
            service_name=service_name,
            available_count=len(all_services),
        )
        click.echo(f"Error: Service '{service_name}' not found.", err=True)
        sys.exit(1)

    service = all_services[service_name]

    # Stop the service first if running
    if not keep_running:
        project_name = get_project_name()

        click.echo(f"Stopping {service_name}...")
        logger.info(
            "services_remove_stop_started",
            project_name=project_name,
            service_name=service_name,
        )

        try:
            cmd = compose_base_cmd(
                phlo_dir=phlo_dir,
                project_name=project_name,
                profiles=() if not service.profile else (service.profile,),
            )
            cmd.extend(["stop", service_name])
            result = run_command(cmd, check=False, capture_output=False)
            if result.returncode != 0:
                logger.warning(
                    "services_remove_stop_failed",
                    project_name=project_name,
                    service_name=service_name,
                    returncode=result.returncode,
                )
            else:
                logger.info(
                    "services_remove_stop_completed",
                    project_name=project_name,
                    service_name=service_name,
                )
        except (FileNotFoundError, TimeoutExpired, OSError) as exc:
            logger.warning(
                "services_remove_stop_exception",
                project_name=project_name,
                service_name=service_name,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            click.echo(f"Warning: Could not stop {service_name}.", err=True)

    # Update config
    enabled, disabled = normalize_services_enabled_disabled_config(config)
    canonical_service_name = service.name

    dependent_names = _dependent_closure(all_services, canonical_service_name)
    names_to_disable = [canonical_service_name, *dependent_names]

    # Remove from enabled if present; add to disabled.
    enabled = [name for name in enabled if name not in names_to_disable]
    disabled.extend(names_to_disable)
    config["services"]["enabled"] = enabled
    config["services"]["disabled"] = disabled
    normalize_services_enabled_disabled_config(config)

    # Write updated config
    with config_file.open("w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    logger.info("services_remove_config_updated", service_name=service_name)

    if dependent_names:
        click.echo(
            f"Removed '{service_name}' and dependent services from phlo.yaml: "
            + ", ".join(dependent_names)
        )
    else:
        click.echo(f"Removed '{service_name}' from phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)
    logger.info("services_remove_completed", service_name=service_name)

    click.echo(f"Service '{service_name}' removed.")
