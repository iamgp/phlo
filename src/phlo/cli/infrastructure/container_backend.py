from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

BackendName = Literal["docker", "podman", "auto"]


@dataclass(frozen=True)
class ContainerInfo:
    service: str
    name: str
    state: str
    labels: dict[str, str]
    ports: str


class ContainerBackend(Protocol):
    name: str

    def compose_base_cmd(
        self,
        *,
        phlo_dir: Path,
        project_name: str,
        profiles: tuple[str, ...] = (),
    ) -> list[str]:
        """Return base compose command tokens."""

    def check_available(self) -> tuple[bool, str | None]:
        """Return availability and remediation message."""

    def list_project_containers(self, project_name: str) -> list[ContainerInfo]:
        """Return containers for a compose project."""


def _compose_base_cmd(
    *,
    binary: str,
    phlo_dir: Path,
    project_name: str,
    profiles: tuple[str, ...] = (),
) -> list[str]:
    compose_file = phlo_dir / "docker-compose.yml"
    env_file = phlo_dir / ".env"
    env_local_file = phlo_dir / ".env.local"
    cmd = [
        binary,
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose_file),
        "--env-file",
        str(env_file),
    ]
    if env_local_file.exists():
        cmd.extend(["--env-file", str(env_local_file)])
    for profile in profiles:
        cmd.extend(["--profile", profile])
    return cmd


def _parse_docker_labels(labels: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in labels.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parsed[key] = value
    return parsed


def _coerce_podman_name(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "")


class DockerBackend:
    name = "docker"

    def compose_base_cmd(
        self,
        *,
        phlo_dir: Path,
        project_name: str,
        profiles: tuple[str, ...] = (),
    ) -> list[str]:
        return _compose_base_cmd(
            binary=self.name,
            phlo_dir=phlo_dir,
            project_name=project_name,
            profiles=profiles,
        )

    def check_available(self) -> tuple[bool, str | None]:
        if shutil.which("docker") is None:
            return False, "Install Docker Desktop or ensure docker is on PATH."
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Install Docker Compose v2 or update Docker Desktop."
        return True, None

    def list_project_containers(self, project_name: str) -> list[ContainerInfo]:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
                "--format",
                "{{json .}}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        containers: list[ContainerInfo] = []
        for line in result.stdout.strip().splitlines():
            info = json.loads(line)
            labels = _parse_docker_labels(info.get("Labels", ""))
            service = labels.get("com.docker.compose.service", "")
            if not service:
                continue
            containers.append(
                ContainerInfo(
                    service=service,
                    name=info.get("Names", ""),
                    state=info.get("State", ""),
                    labels=labels,
                    ports=info.get("Ports", ""),
                )
            )
        return containers


class PodmanBackend:
    name = "podman"

    def compose_base_cmd(
        self,
        *,
        phlo_dir: Path,
        project_name: str,
        profiles: tuple[str, ...] = (),
    ) -> list[str]:
        return _compose_base_cmd(
            binary=self.name,
            phlo_dir=phlo_dir,
            project_name=project_name,
            profiles=profiles,
        )

    def check_available(self) -> tuple[bool, str | None]:
        if shutil.which("podman") is None:
            return False, "Install Podman Desktop or ensure podman is on PATH."
        info = subprocess.run(
            ["podman", "info"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if info.returncode != 0:
            return False, "Start Podman with `podman machine start`, then retry."
        compose = subprocess.run(
            ["podman", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if compose.returncode != 0:
            return False, "Install or configure a Podman compose provider."
        return True, None

    def list_project_containers(self, project_name: str) -> list[ContainerInfo]:
        result = subprocess.run(
            [
                "podman",
                "ps",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        containers: list[ContainerInfo] = []
        for info in json.loads(result.stdout):
            raw_labels = info.get("Labels", {}) or {}
            labels = {str(key): str(value) for key, value in raw_labels.items()}
            service = labels.get("com.docker.compose.service") or labels.get(
                "io.podman.compose.service", ""
            )
            if not service:
                continue
            containers.append(
                ContainerInfo(
                    service=service,
                    name=_coerce_podman_name(info.get("Names")),
                    state=str(info.get("State", "")),
                    labels=labels,
                    ports=str(info.get("Ports", "")),
                )
            )
        return containers


def select_container_backend(
    *,
    cli_backend: str | None,
    config_backend: str | None,
) -> ContainerBackend:
    selected = (
        cli_backend or os.environ.get("PHLO_CONTAINER_BACKEND") or config_backend or "docker"
    ).strip()
    if selected == "auto":
        selected = "docker" if shutil.which("docker") else "podman"
    if selected == "docker":
        return DockerBackend()
    if selected == "podman":
        return PodmanBackend()
    raise ValueError(f"Unsupported container backend: {selected}")
