"""List command for showing available services."""

import json
import subprocess
from pathlib import Path

import click
import yaml

from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery

logger = get_logger(__name__)


def _extract_compose_service(container_info: dict) -> str | None:
    """Extract the compose service name from docker ps JSON output.

    Uses the ``com.docker.compose.service`` label when available,
    falling back to container-name parsing for non-compose containers.
    """
    labels = container_info.get("Labels", "")
    for label in labels.split(","):
        if label.startswith("com.docker.compose.service="):
            return label.split("=", 1)[1]
    return None


@click.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all services including optional")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_cmd(show_all: bool, output_json: bool):
    """List available services with status and configuration.

    Examples:
        phlo services list
        phlo services list --all
        phlo services list --json
    """
    # Load phlo.yaml for user overrides
    config_file = Path.cwd() / "phlo.yaml"
    user_overrides = {}
    logger.info(
        "services_list_requested",
        show_all=show_all,
        output_json=output_json,
    )
    if config_file.exists():
        try:
            with open(config_file) as f:
                existing_config = yaml.safe_load(f) or {}
                user_overrides = existing_config.get("services", {})
        except (OSError, yaml.YAMLError) as exc:
            logger.error(
                "services_list_config_read_failed",
                config_file=str(config_file),
                exc_info=True,
            )
            raise click.ClickException(
                f"Failed to read {config_file}. Check YAML syntax and file permissions, then retry."
            ) from exc

    # Discover available services
    try:
        discovery = ServiceDiscovery()
        available_services = discovery.discover()
    except Exception as exc:
        logger.error("services_list_discovery_failed", exc_info=True)
        raise click.ClickException(
            "Failed to discover services. Verify service plugins are installed and run "
            "`phlo plugins list` for diagnostics."
        ) from exc

    # Check which services are disabled
    disabled_services = {
        name
        for name, cfg in user_overrides.items()
        if isinstance(cfg, dict) and cfg.get("enabled") is False
    }

    # Collect inline custom services
    inline_services = []
    for name, cfg in user_overrides.items():
        if isinstance(cfg, dict) and cfg.get("type") == "inline":
            inline_services.append(ServiceDefinition.from_inline(name, cfg))

    # Get running container status using compose project label for deterministic matching
    try:
        project_name = get_project_name()
        result = run_command(
            [
                "docker",
                "ps",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
                "--format",
                "{{json .}}",
            ],
            check=False,
        )
        running_containers = {}
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                container_info = json.loads(line)
                service_name = _extract_compose_service(container_info)
                if service_name:
                    running_containers[service_name] = {
                        "status": container_info.get("State", ""),
                        "ports": container_info.get("Ports", ""),
                    }
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, ValueError):
        logger.warning(
            "services_list_runtime_status_unavailable",
            project_name=get_project_name(),
            exc_info=True,
        )
        running_containers = {}

    if output_json:
        all_services = list(available_services.values()) + inline_services
        payload = [
            {
                "name": svc.name,
                "description": svc.description,
                "category": svc.category,
                "default": svc.default,
                "profile": svc.profile,
                "depends_on": svc.depends_on,
                "compose": svc.compose,
                "env_vars": svc.env_vars,
                "core": svc.core,
                "disabled": svc.name in disabled_services,
                "inline": svc in inline_services,
                "running": svc.name in running_containers,
            }
            for svc in all_services
        ]
        logger.info(
            "services_list_json_completed",
            total_services=len(payload),
            running_count=sum(1 for svc in payload if svc["running"]),
            disabled_count=sum(1 for svc in payload if svc["disabled"]),
        )
        click.echo(json.dumps(payload, indent=2))
        return

    # Helper to format service line
    def format_service_line(svc, custom_status=None):
        """Format a service line with status, ports, and description."""
        if svc.name in disabled_services:
            status_marker = "✗"
            status = "Disabled"
            ports = ""
            suffix = "(disabled in phlo.yaml)"
        elif svc.name in running_containers:
            status_marker = "✓"
            status = "Running"
            container = running_containers[svc.name]
            port_str = container.get("ports", "")
            # Extract first exposed port (format: "0.0.0.0:3000->3000/tcp")
            if "->" in port_str:
                external_port = port_str.split("->")[0].split(":")[-1]
                ports = f":{external_port}"
            else:
                ports = ""
            suffix = ""
        else:
            status_marker = " "
            status = "Stopped"
            ports = ""
            suffix = ""

        if custom_status:
            suffix = custom_status

        # Format: "  ✓ service-name    Running    :3000   Description [extra]"
        name_col = f"{svc.name:<18}"
        status_col = f"{status:<10}"
        ports_col = f"{ports:<7}"
        desc_with_suffix = f"{svc.description} {suffix}".strip()

        return f"  {status_marker} {name_col} {status_col} {ports_col} {desc_with_suffix}"

    # Separate services by type
    package_services = [s for s in available_services.values() if not s.core]

    # Display package services
    if package_services or disabled_services:
        click.echo("\nPackage Services (installed):")
        displayed = set()
        for svc in sorted(package_services, key=lambda x: x.name):
            if not show_all and svc.profile and not svc.default:
                continue
            click.echo(format_service_line(svc))
            displayed.add(svc.name)

        # Show disabled services that aren't in the package list
        for name in sorted(disabled_services):
            if name not in displayed and name in available_services:
                svc = available_services[name]
                click.echo(format_service_line(svc))

    # Display inline custom services
    if inline_services:
        click.echo("\nCustom Services (phlo.yaml):")
        for svc in sorted(inline_services, key=lambda x: x.name):
            click.echo(format_service_line(svc, custom_status="(inline)"))

    logger.info(
        "services_list_completed",
        available_count=len(available_services),
        inline_count=len(inline_services),
        running_count=len(running_containers),
        disabled_count=len(disabled_services),
    )
    click.echo("")
