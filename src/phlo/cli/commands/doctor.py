from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import click
import yaml

from phlo.plugins.discovery import ServiceDiscovery


class DiagnosticStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass(frozen=True)
class DiagnosticResult:
    id: str
    group: str
    status: DiagnosticStatus
    message: str
    fix: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "group": self.group,
            "status": self.status.value,
            "message": self.message,
        }
        if self.fix:
            payload["fix"] = self.fix
        if self.details:
            payload["details"] = self.details
        return payload


def summarize(results: list[DiagnosticResult]) -> dict[str, int]:
    return {
        status.value: sum(1 for result in results if result.status == status)
        for status in DiagnosticStatus
    }


def render_json(results: list[DiagnosticResult]) -> str:
    return json.dumps(
        {
            "summary": summarize(results),
            "checks": [result.to_payload() for result in results],
        },
        indent=2,
        sort_keys=True,
    )


def render_terminal(results: list[DiagnosticResult]) -> str:
    lines = ["Phlo Doctor", ""]
    groups = list(dict.fromkeys(result.group for result in results))
    for group in groups:
        lines.append(group)
        for result in [item for item in results if item.group == group]:
            lines.append(f"  {result.status.value:<5} {result.message}")
            if result.fix:
                lines.append(f"        Fix: {result.fix}")
        lines.append("")
    summary = summarize(results)
    lines.append(
        "Summary: "
        f"{summary['ok']} ok, {summary['warn']} warnings, "
        f"{summary['fail']} failures, {summary['skip']} skipped"
    )
    return "\n".join(lines)


def _run_probe(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)


def check_environment(*, verbose: bool = False) -> list[DiagnosticResult]:
    results: list[DiagnosticResult] = [
        DiagnosticResult(
            "doctor.bootstrap", "Environment", DiagnosticStatus.OK, "Doctor command loaded"
        )
    ]
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_status = DiagnosticStatus.OK if sys.version_info >= (3, 11) else DiagnosticStatus.FAIL
    results.append(
        DiagnosticResult(
            "env.python",
            "Environment",
            python_status,
            f"Python {python_version}",
            None if python_status == DiagnosticStatus.OK else "Install Python 3.11 or newer.",
        )
    )

    uv_path = shutil.which("uv")
    results.append(
        DiagnosticResult(
            "env.uv",
            "Environment",
            DiagnosticStatus.OK if uv_path else DiagnosticStatus.FAIL,
            "uv found" if uv_path else "uv command not found",
            None if uv_path else "Install uv from https://docs.astral.sh/uv/.",
        )
    )

    docker_path = shutil.which("docker")
    results.append(
        DiagnosticResult(
            "env.docker.cli",
            "Environment",
            DiagnosticStatus.OK if docker_path else DiagnosticStatus.FAIL,
            "Docker CLI found" if docker_path else "Docker CLI not found",
            None if docker_path else "Install Docker Desktop or ensure docker is on PATH.",
        )
    )

    if docker_path:
        compose = _run_probe(["docker", "compose", "version"])
        details = {"stderr": compose.stderr.strip()} if verbose and compose.stderr else {}
        results.append(
            DiagnosticResult(
                "env.docker.compose",
                "Environment",
                DiagnosticStatus.OK if compose.returncode == 0 else DiagnosticStatus.FAIL,
                "Docker Compose available"
                if compose.returncode == 0
                else "Docker Compose is not available",
                None
                if compose.returncode == 0
                else "Install Docker Compose v2 or update Docker Desktop.",
                details,
            )
        )

    _, _, free = shutil.disk_usage(Path.cwd())
    free_gb = free // (1024**3)
    results.append(
        DiagnosticResult(
            "env.disk",
            "Environment",
            DiagnosticStatus.OK if free_gb >= 10 else DiagnosticStatus.WARN,
            f"{free_gb} GB free in current filesystem",
            None if free_gb >= 10 else "Free at least 10 GB before starting the full local stack.",
        )
    )
    return results


def check_project(*, verbose: bool = False) -> list[DiagnosticResult]:
    results: list[DiagnosticResult] = []
    project_file = Path.cwd() / "phlo.yaml"
    if not project_file.exists():
        return [
            DiagnosticResult(
                "project.config",
                "Project",
                DiagnosticStatus.SKIP,
                "phlo.yaml not found",
                "Run this command inside a Phlo project, or create one with phlo init.",
            )
        ]

    try:
        loaded = yaml.safe_load(project_file.read_text()) or {}
        status = DiagnosticStatus.OK if isinstance(loaded, dict) else DiagnosticStatus.FAIL
        results.append(
            DiagnosticResult(
                "project.config",
                "Project",
                status,
                "phlo.yaml parsed"
                if status == DiagnosticStatus.OK
                else "phlo.yaml must contain a mapping",
                None
                if status == DiagnosticStatus.OK
                else "Fix phlo.yaml so the top level is a YAML mapping.",
            )
        )
    except (OSError, yaml.YAMLError) as exc:
        results.append(
            DiagnosticResult(
                "project.config",
                "Project",
                DiagnosticStatus.FAIL,
                "phlo.yaml could not be read or parsed",
                "Fix YAML syntax and file permissions, then rerun phlo doctor.",
                {"error": str(exc)} if verbose else {},
            )
        )

    phlo_dir = Path.cwd() / ".phlo"
    compose_file = phlo_dir / "docker-compose.yml"
    results.append(
        DiagnosticResult(
            "project.compose",
            "Project",
            DiagnosticStatus.OK if compose_file.exists() else DiagnosticStatus.WARN,
            ".phlo/docker-compose.yml found"
            if compose_file.exists()
            else ".phlo/docker-compose.yml is missing",
            None if compose_file.exists() else "Run phlo services init.",
        )
    )
    for filename in (".env", ".env.local"):
        path = phlo_dir / filename
        results.append(
            DiagnosticResult(
                f"project.{filename}",
                "Project",
                DiagnosticStatus.OK if path.exists() else DiagnosticStatus.WARN,
                f".phlo/{filename} found" if path.exists() else f".phlo/{filename} is missing",
                None if path.exists() else "Run phlo services init.",
            )
        )
    return results


def check_discovery(*, verbose: bool = False) -> list[DiagnosticResult]:
    try:
        services = ServiceDiscovery().discover()
    except Exception as exc:
        return [
            DiagnosticResult(
                "discovery.services",
                "Discovery",
                DiagnosticStatus.FAIL,
                "Service discovery failed",
                "Run phlo doctor --verbose to inspect the discovery exception.",
                {"error": str(exc), "type": type(exc).__name__} if verbose else {},
            )
        ]
    return [
        DiagnosticResult(
            "discovery.services",
            "Discovery",
            DiagnosticStatus.OK,
            f"Discovered {len(services)} services",
        )
    ]


def run_diagnostics(*, verbose: bool = False) -> list[DiagnosticResult]:
    return [
        *check_environment(verbose=verbose),
        *check_project(verbose=verbose),
        *check_discovery(verbose=verbose),
    ]


@click.command("doctor")
@click.option("--json", "output_json", is_flag=True, help="Output diagnostics as JSON.")
@click.option("--verbose", is_flag=True, help="Include exception details where available.")
def doctor_cmd(output_json: bool, verbose: bool) -> None:
    """Diagnose local Phlo setup and service health."""
    results = run_diagnostics(verbose=verbose)
    click.echo(render_json(results) if output_json else render_terminal(results))
    if any(result.status == DiagnosticStatus.FAIL for result in results):
        raise click.exceptions.Exit(1)
