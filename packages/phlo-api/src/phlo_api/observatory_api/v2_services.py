"""Service read models for Observatory v2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import http.client
import json
import os
from pathlib import Path
import re
import socket
import subprocess
from typing import Any

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import (
    HealthState,
    ServiceStatus,
    V2ExternalLink,
    V2Health,
    V2Service,
    V2ServiceConfigEntry,
    V2ServicePort,
)

DOCKER_SOCKET = "/var/run/docker.sock"
DOCKER_SERVICE_STATUS_RANK: dict[ServiceStatus, int] = {
    "running": 4,
    "unhealthy": 3,
    "starting": 2,
    "stopped": 1,
    "unknown": 0,
}
ENV_DEFAULT_RE = re.compile(r"^\$\{[^}:]+:-(?P<default>[^}]+)\}$")


def coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def fallback_services() -> list[V2Service]:
    """Return deterministic service data without package-specific imports."""
    return [
        V2Service(
            id="phlo-api",
            name="phlo-api",
            kind="api",
            status="unknown",
            health=V2Health(state="unknown", message="Runtime status unavailable"),
            definition_state="configured",
            runtime_state="unknown",
            in_stack=True,
            backend="native",
            impacts=["observatory"],
            metadata={"source": "fallback", "core": True},
        ),
        V2Service(
            id="observatory",
            name="observatory",
            kind="ui",
            status="unknown",
            health=V2Health(state="unknown", message="Runtime status unavailable"),
            definition_state="configured",
            runtime_state="unknown",
            in_stack=True,
            backend="native",
            depends_on=["phlo-api"],
            metadata={"source": "fallback", "core": True},
        ),
    ]


def docker_status_from_container(
    container: Mapping[str, Any],
) -> tuple[ServiceStatus, V2Health]:
    state = coerce_str(container.get("State"), "unknown").lower()
    status_text = coerce_str(container.get("Status"), "")
    status_lower = status_text.lower()

    if state == "running" and "(unhealthy)" in status_lower:
        return "unhealthy", V2Health(state="error", message=status_text)
    if state == "running" and "starting" in status_lower:
        return "starting", V2Health(state="warning", message=status_text)
    if state == "running":
        health: HealthState = "ok" if "(healthy)" in status_lower else "unknown"
        return "running", V2Health(state=health, message=status_text or None)
    if state in {"created", "restarting"}:
        return "starting", V2Health(state="warning", message=status_text or state)
    if state == "exited" and "exited (0)" in status_lower:
        return "stopped", V2Health(state="ok", message=status_text or "Completed")
    if state in {"exited", "dead", "removing"}:
        return "stopped", V2Health(state="warning", message=status_text or state)
    return "unknown", V2Health(state="unknown", message=status_text or None)


def container_labels(container: Mapping[str, Any]) -> dict[str, str]:
    labels = container.get("Labels")
    if isinstance(labels, Mapping):
        return {str(key): str(value) for key, value in labels.items()}
    if not isinstance(labels, str) or not labels:
        return {}
    parsed: dict[str, str] = {}
    for item in labels.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed


class UnixSocketHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        self.sock = sock


def docker_socket_json(path: str, socket_path: str = DOCKER_SOCKET) -> Any:
    connection = UnixSocketHTTPConnection(socket_path)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        if response.status >= 400:
            return None
        body = response.read().decode()
        return json.loads(body) if body else None
    except (OSError, json.JSONDecodeError, http.client.HTTPException):
        return None
    finally:
        connection.close()


def normalize_docker_api_container(container: Mapping[str, Any]) -> dict[str, Any]:
    names = container.get("Names")
    if isinstance(names, list) and names:
        name = str(names[0]).lstrip("/")
    else:
        name = coerce_str(container.get("Names") or container.get("Name"), "").lstrip("/")
    return {
        "ID": coerce_str(container.get("Id") or container.get("ID"), ""),
        "Names": name,
        "State": coerce_str(container.get("State"), ""),
        "Status": coerce_str(container.get("Status"), ""),
        "Labels": container.get("Labels") if isinstance(container.get("Labels"), Mapping) else {},
    }


def load_docker_containers() -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None

    if result is not None and result.returncode == 0:
        containers: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, Mapping):
                containers.append(dict(parsed))
        return containers

    if not Path(DOCKER_SOCKET).exists():
        return []
    payload = docker_socket_json("/containers/json?all=1")
    if not isinstance(payload, list):
        return []
    return [
        normalize_docker_api_container(container)
        for container in payload
        if isinstance(container, Mapping)
    ]


def current_compose_project(containers: Sequence[Mapping[str, Any]]) -> str | None:
    configured = os.environ.get("PHLO_COMPOSE_PROJECT") or os.environ.get("COMPOSE_PROJECT_NAME")
    if configured:
        return configured

    hostname = os.environ.get("HOSTNAME", "")
    if not hostname:
        return None

    for container in containers:
        container_id = coerce_str(container.get("ID") or container.get("Id"), "")
        if container_id and container_id.startswith(hostname):
            labels = container_labels(container)
            project = labels.get("com.docker.compose.project")
            if project:
                return project

    inspected = docker_socket_json(f"/containers/{hostname}/json")
    if isinstance(inspected, Mapping):
        config = inspected.get("Config")
        labels = config.get("Labels") if isinstance(config, Mapping) else None
        if isinstance(labels, Mapping):
            project = labels.get("com.docker.compose.project")
            if project:
                return str(project)
    return None


def compose_service_name(container: Mapping[str, Any]) -> str | None:
    labels = container_labels(container)
    service_name = labels.get("com.docker.compose.service")
    if service_name:
        return service_name
    name = coerce_str(container.get("Names"), "")
    if name.endswith("-1") and "-" in name:
        return name.rsplit("-", 2)[-2]
    return None


def service_name_from_container(name: str, service_ids: set[str]) -> str | None:
    ordered_service_ids = list(service_ids)
    ordered_service_ids.sort(key=lambda value: len(value), reverse=True)
    for service_id in ordered_service_ids:
        if name == service_id or name.endswith(f"-{service_id}-1"):
            return service_id
    return None


def load_docker_service_statuses(
    service_ids: set[str],
    containers: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, tuple[ServiceStatus, V2Health]]:
    if not service_ids:
        return {}

    statuses: dict[str, tuple[ServiceStatus, V2Health]] = {}
    containers = containers if containers is not None else load_docker_containers()
    compose_project = current_compose_project(containers)
    for container in containers:
        if compose_project:
            labels = container_labels(container)
            if labels.get("com.docker.compose.project") != compose_project:
                continue
        name = coerce_str(container.get("Names"), "")
        service_id = compose_service_name(container) or service_name_from_container(
            name, service_ids
        )
        if service_id not in service_ids:
            service_id = service_name_from_container(name, service_ids)
        if service_id is None:
            continue
        status, health = docker_status_from_container(container)
        current = statuses.get(service_id)
        if (
            current is None
            or DOCKER_SERVICE_STATUS_RANK[status] > DOCKER_SERVICE_STATUS_RANK[current[0]]
        ):
            statuses[service_id] = (status, health)
    return statuses


def runtime_services_from_containers(
    containers: Sequence[Mapping[str, Any]],
    known_ids: set[str],
) -> list[V2Service]:
    compose_project = current_compose_project(containers)
    services: list[V2Service] = []
    for container in containers:
        labels = container_labels(container)
        if compose_project and labels.get("com.docker.compose.project") != compose_project:
            continue
        service_id = compose_service_name(container)
        if not service_id or service_id in known_ids:
            continue
        status, health = docker_status_from_container(container)
        services.append(
            V2Service(
                id=service_id,
                name=service_id,
                kind=labels.get("phlo.service.category", "service"),
                status=status,
                health=health,
                definition_state="configured",
                runtime_state=status,
                in_stack=True,
                backend="docker",
                metadata=safe_metadata({"source": "docker", "compose_project": compose_project}),
            )
        )
        known_ids.add(service_id)
    return services


def service_links_from_definition(service: Any) -> list[V2ExternalLink]:
    compose = getattr(service, "compose", {}) if service is not None else {}
    labels = compose.get("labels") if isinstance(compose, Mapping) else {}
    ports = compose.get("ports") if isinstance(compose, Mapping) else []
    links: list[V2ExternalLink] = []

    if isinstance(labels, Mapping):
        for key, value in labels.items():
            if str(key).endswith(".rule") and "Host(`" in str(value):
                host = str(value).split("Host(`", 1)[1].split("`)", 1)[0]
                if host and "$" not in host:
                    links.append(V2ExternalLink(label="Open", url=f"http://{host}", kind="app"))

    for port in ports if isinstance(ports, list) else []:
        if not isinstance(port, str) or ":" not in port:
            continue
        published = resolve_env_default(port.split(":", 1)[0])
        target = port.rsplit(":", 1)[-1]
        if published.isdigit():
            links.append(
                V2ExternalLink(
                    label=f":{target}",
                    url=f"http://localhost:{published}",
                    kind="port",
                )
            )

    return links[:4]


def service_ports_from_definition(service: Any) -> list[V2ServicePort]:
    compose = getattr(service, "compose", {}) if service is not None else {}
    ports = compose.get("ports") if isinstance(compose, Mapping) else []
    exposed: list[V2ServicePort] = []
    for index, port in enumerate(ports if isinstance(ports, list) else []):
        if not isinstance(port, str):
            continue
        if ":" in port:
            published, target = port.rsplit(":", 1)
        else:
            published, target = None, port
        exposed.append(
            V2ServicePort(
                name=f"port-{index + 1}",
                published=resolve_env_default(published) if published else None,
                target=target,
            )
        )
    return exposed


def resolve_env_default(value: str) -> str:
    match = ENV_DEFAULT_RE.match(value)
    if match is not None:
        return match.group("default")
    return value


def service_config_from_definition(service: Any) -> list[V2ServiceConfigEntry]:
    env_vars = getattr(service, "env_vars", {}) if service is not None else {}
    if not isinstance(env_vars, Mapping):
        return []

    entries: list[V2ServiceConfigEntry] = []
    for name, config in sorted(env_vars.items()):
        if not isinstance(config, Mapping):
            continue
        secret = bool(config.get("secret"))
        entries.append(
            V2ServiceConfigEntry(
                name=str(name),
                value=None if secret else coerce_str(config.get("default"), "") or None,
                description=coerce_str(config.get("description"), "") or None,
                secret=secret,
            )
        )
    return entries[:12]


def load_services(
    project_root: Path,
    containers: Sequence[Mapping[str, Any]] | None = None,
) -> list[V2Service]:
    """Load services through core discovery, falling back deterministically."""
    _ = project_root
    try:
        from phlo.plugins.discovery import ServiceDiscovery

        discovered = ServiceDiscovery().discover().values()
    except Exception:
        discovered = []

    services: list[V2Service] = []
    containers = containers if containers is not None else load_docker_containers()
    discovered = list(discovered)
    runtime_statuses = load_docker_service_statuses(
        {service.name for service in discovered},
        containers,
    )
    for service in discovered:
        in_stack = service.name in runtime_statuses
        status, health = runtime_statuses.get(
            service.name,
            ("unknown", V2Health(state="unknown", message="Runtime status unavailable")),
        )
        services.append(
            V2Service(
                id=service.name,
                name=service.name,
                kind=service.category or "service",
                status=status,
                health=health,
                definition_state="configured" if in_stack else "available",
                runtime_state=status,
                in_stack=in_stack,
                disabled=bool(getattr(service, "disabled", False)),
                profile=coerce_str(service.profile, "") or None,
                backend="docker" if in_stack else "unknown",
                depends_on=list(service.depends_on or []),
                impacts=[],
                links=service_links_from_definition(service),
                metadata=safe_metadata(
                    {
                        "default": bool(service.default),
                        "profile": service.profile,
                        "core": bool(getattr(service, "core", False)),
                        "description": getattr(service, "description", None),
                    }
                ),
            )
        )

    services.extend(
        runtime_services_from_containers(containers, {service.id for service in services})
    )

    return sorted(services, key=lambda item: item.id) if services else fallback_services()
