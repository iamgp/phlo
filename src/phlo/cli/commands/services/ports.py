"""Ports command for showing service port mappings."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click
import yaml

from phlo.cli.commands.services.utils import _get_env_overrides, get_enabled_disabled_service_names
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.utils import get_project_name, parse_env_file
from phlo.logging import get_logger
from phlo.plugins.discovery import ServiceDefinition, ServiceDiscovery

logger = get_logger(__name__)

PORT_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}:(\d+)")
DEFAULT_PORT_PATTERN = re.compile(r"\$\{([^}:]+):-(\d+)\}")


@dataclass
class PortMapping:
    """Represents a resolved port mapping for a service."""

    service: str
    host_port: int
    container_port: int
    source: str
    status: str
    env_var: str | None = None


@dataclass
class ComposePortSpec:
    """Represents a parsed compose port mapping."""

    env_var: str | None
    host_port: str | None
    container_port: str


def _parse_compose_port(port_str: str) -> tuple[str | None, str]:
    """Parse a compose port string into (env_var, container_port).

    Format: "${VAR:-default}:container" or "host:container"
    """
    spec = _parse_compose_port_spec(port_str)
    return (spec.env_var, spec.container_port)


def _parse_compose_port_spec(port_str: str) -> ComposePortSpec:
    """Parse a compose port string into its env/literal host and container parts."""
    normalized = port_str.strip().strip("\"'")
    match = PORT_PATTERN.match(normalized)
    if match:
        return ComposePortSpec(
            env_var=match.group(1),
            host_port=match.group(2),
            container_port=match.group(3),
        )

    if ":" in normalized:
        host_part, container_part = normalized.rsplit(":", 1)
        return ComposePortSpec(
            env_var=None,
            host_port=host_part.rsplit(":", 1)[-1],
            container_port=container_part.split("/", 1)[0],
        )

    return ComposePortSpec(env_var=None, host_port=None, container_port=normalized)


def _resolve_env_var(env_var: str | None, env: dict[str, str]) -> str | None:
    """Resolve an environment variable from the loaded environment."""
    if env_var is None:
        return None
    return env.get(env_var)


def _load_environment(phlo_dir: Path, config: dict[str, Any]) -> dict[str, str]:
    """Load effective compose environment with standard Phlo precedence."""
    env: dict[str, str] = {}

    env_file = phlo_dir / ".env"
    env_local_file = phlo_dir / ".env.local"

    for file_path in [env_file, env_local_file]:
        if file_path.exists():
            parsed = parse_env_file(file_path)
            env.update(parsed)

    env.update({k: str(v) for k, v in _get_env_overrides(config).items() if isinstance(k, str)})
    env.update(os.environ)

    return env


def _get_running_container_ports(project_name: str) -> dict[str, list[dict]]:
    """Get published ports from running containers."""
    try:
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
        containers = {}
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                info = json.loads(line)
                service = None
                for label in info.get("Labels", "").split(","):
                    if label.startswith("com.docker.compose.service="):
                        service = label.split("=", 1)[1]
                        break
                if service:
                    ports_str = info.get("Ports", "")
                    port_mappings: list[dict[str, str]] = []
                    if ports_str:
                        for port_entry in ports_str.split(", "):
                            if "->" in port_entry:
                                host_part, container_part = port_entry.split("->")
                                host_ip = (
                                    host_part.rsplit(":", 1)[0] if ":" in host_part else "0.0.0.0"
                                )
                                host_port = (
                                    host_part.rsplit(":", 1)[-1] if ":" in host_part else host_part
                                )
                                port_mappings.append(
                                    {
                                        "host_port": host_port,
                                        "host_ip": host_ip,
                                        "container_port": container_part,
                                    }
                                )
                    containers[service] = {
                        "status": info.get("State", "running"),
                        "ports": port_mappings,
                    }
        return containers
    except Exception:
        logger.warning("docker_ps_failed", exc_info=True)
        return {}


def _get_runtime_host_port(
    running_containers: dict[str, Any],
    service_name: str,
    container_port: int,
) -> int | None:
    """Return the live host port for a running container port mapping, if present."""
    container_info = running_containers.get(service_name, {})
    for port_mapping in container_info.get("ports", []):
        container_value = str(port_mapping.get("container_port", "")).split("/", 1)[0]
        if container_value != str(container_port):
            continue
        host_port = port_mapping.get("host_port")
        if host_port and str(host_port).isdigit():
            return int(host_port)
    return None


def _get_default_host_port(port_str: str, port_spec: ComposePortSpec) -> int | None:
    """Resolve a configured host port from a compose mapping when no runtime mapping exists."""
    if port_spec.host_port and port_spec.host_port.isdigit():
        return int(port_spec.host_port)

    if port_spec.env_var:
        default_match = DEFAULT_PORT_PATTERN.search(port_str)
        if default_match:
            return int(default_match.group(2))

    return None


def _get_service_ports(
    service: ServiceDefinition,
    env: dict[str, str],
    running_containers: dict[str, Any],
    show_all: bool,
    service_override: dict[str, Any] | None = None,
) -> list[PortMapping]:
    """Get port mappings for a service."""
    ports: list[PortMapping] = []
    compose_ports = service.compose.get("ports", [])
    if isinstance(service_override, dict) and service_override.get("ports"):
        compose_ports = service_override["ports"]

    if not compose_ports:
        return ports

    is_running = service.name in running_containers
    if not show_all and not is_running:
        return ports

    for port_str in compose_ports:
        port_spec = _parse_compose_port_spec(port_str)
        container_port = int(port_spec.container_port)

        resolved_host_port: int | None = None
        source = "default"
        resolved_env_var: str | None = None

        if is_running:
            resolved_host_port = _get_runtime_host_port(
                running_containers, service.name, container_port
            )
            if resolved_host_port is not None:
                source = "runtime"

        if resolved_host_port is None and port_spec.env_var:
            resolved_value = _resolve_env_var(port_spec.env_var, env)
            if resolved_value and resolved_value.isdigit():
                resolved_host_port = int(resolved_value)
                source = "env"
                resolved_env_var = port_spec.env_var

        if resolved_host_port is None:
            resolved_host_port = _get_default_host_port(port_str, port_spec)
            if resolved_host_port is not None and port_spec.env_var is None and port_spec.host_port:
                source = "compose"

        if resolved_host_port is None:
            continue

        status = "Running" if is_running else "Stopped"

        ports.append(
            PortMapping(
                service=service.name,
                host_port=resolved_host_port,
                container_port=container_port,
                source=source,
                status=status,
                env_var=resolved_env_var,
            )
        )

    return ports


def _detect_conflicts(port_mappings: list[PortMapping]) -> list[tuple[str, str, int]]:
    """Detect port conflicts. Returns list of (service1, service2, port) tuples."""
    host_port_to_services: dict[int, list[str]] = {}
    for pm in port_mappings:
        if pm.host_port not in host_port_to_services:
            host_port_to_services[pm.host_port] = []
        if pm.service not in host_port_to_services[pm.host_port]:
            host_port_to_services[pm.host_port].append(pm.service)

    conflicts = []
    for port, services in host_port_to_services.items():
        if len(services) > 1:
            for i in range(len(services) - 1):
                conflicts.append((services[i], services[i + 1], port))
    return conflicts


def _format_table(port_mappings: list[PortMapping], conflicts: list[tuple[str, str, int]]) -> None:
    """Format and print the port table."""
    if not port_mappings:
        click.echo("No port mappings found.")
        return

    conflict_ports = {c[2] for c in conflicts}

    header = (
        f"{'Service':<20} {'Host Port':<12} {'Container Port':<16} {'Source':<10} {'Status':<10}"
    )
    separator = "-" * 70

    click.echo(header)
    click.echo(separator)

    for pm in sorted(port_mappings, key=lambda x: x.service):
        prefix = "⚠ " if pm.host_port in conflict_ports else "  "
        row = (
            f"{prefix}{pm.service:<18} "
            f"{pm.host_port:<12} "
            f"{pm.container_port:<16} "
            f"{pm.source:<10} "
            f"{pm.status:<10}"
        )
        click.echo(row)

    if conflicts:
        click.echo("")
        for s1, s2, port in conflicts:
            click.echo(f"⚠ Port conflict: {s1} and {s2} both map to host port {port}")


def _format_json(port_mappings: list[PortMapping]) -> None:
    """Format and print JSON output."""
    output = []
    for pm in port_mappings:
        output.append(
            {
                "service": pm.service,
                "host_port": pm.host_port,
                "container_port": pm.container_port,
                "source": pm.source,
                "status": pm.status.lower(),
                "env_var": pm.env_var,
            }
        )
    click.echo(json.dumps(output, indent=2))


@click.command("ports")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--all", "show_all", is_flag=True, help="Include stopped services with defaults")
def ports_cmd(output_json: bool, show_all: bool):
    """Show port mappings for all services.

    Displays host port, container port, source (default/env/runtime), and status.

    Examples:
        phlo services ports
        phlo services ports --json
        phlo services ports --all
    """
    logger.info(
        "services_ports_requested",
        output_json=output_json,
        show_all=show_all,
    )

    phlo_dir = Path.cwd() / ".phlo"
    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found. Run 'phlo services init' first.", err=True)
        raise SystemExit(1)

    config_file = Path.cwd() / "phlo.yaml"
    existing_config: dict = {}
    if config_file.exists():
        try:
            with config_file.open() as f:
                existing_config = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as exc:
            logger.error("config_read_failed", exc_info=True)
            raise click.ClickException(f"Failed to read {config_file}.") from exc

    _, disabled_services = get_enabled_disabled_service_names(existing_config)
    service_overrides = existing_config.get("services", {})

    env = _load_environment(phlo_dir, existing_config)

    try:
        discovery = ServiceDiscovery()
        available_services = discovery.discover()
    except Exception as exc:
        logger.error("services_discovery_failed", exc_info=True)
        raise click.ClickException(
            "Failed to discover services. Verify service plugins are installed."
        ) from exc

    project_name = get_project_name()
    running_containers = _get_running_container_ports(project_name)

    port_mappings: list[PortMapping] = []

    for svc in available_services.values():
        if svc.name in disabled_services:
            continue
        service_override = (
            service_overrides.get(svc.name, {}) if isinstance(service_overrides, dict) else {}
        )
        ports = _get_service_ports(
            svc,
            env,
            running_containers,
            show_all,
            service_override=service_override if isinstance(service_override, dict) else None,
        )
        port_mappings.extend(ports)

    conflicts = _detect_conflicts(port_mappings)

    if output_json:
        _format_json(port_mappings)
    else:
        _format_table(port_mappings, conflicts)

    logger.info(
        "services_ports_completed",
        total_mappings=len(port_mappings),
        conflicts=len(conflicts),
    )
