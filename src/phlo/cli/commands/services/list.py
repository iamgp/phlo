"""List command for showing available services."""

import json
from pathlib import Path

import click
import yaml

from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.utils import get_project_name
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery


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
    if config_file.exists():
        with open(config_file) as f:
            existing_config = yaml.safe_load(f) or {}
            user_overrides = existing_config.get("services", {})

    # Discover available services
    discovery = ServiceDiscovery()
    available_services = discovery.discover()

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

    # Get running container status
    try:
        project_name = get_project_name()
        result = run_command(
            ["docker", "ps", "--filter", f"name={project_name}", "--format", "{{json .}}"],
            check=False,
        )
        running_containers = {}
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                container_info = json.loads(line)
                container_name = container_info.get("Names", "")
                # Extract service name from container name (format: project-service-1)
                # Remove project prefix and container number suffix
                prefix = f"{project_name}-"
                if container_name.startswith(prefix):
                    # Remove prefix and -1 suffix (last dash and number)
                    service_with_suffix = container_name[len(prefix) :]
                    # Remove the -1 suffix
                    service_name = service_with_suffix.rsplit("-", 1)[0]
                    running_containers[service_name] = {
                        "status": container_info.get("State", ""),
                        "ports": container_info.get("Ports", ""),
                    }
    except Exception:
        # Silently handle errors - services list should work even without docker
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

    click.echo("")
