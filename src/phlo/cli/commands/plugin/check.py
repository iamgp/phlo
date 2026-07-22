"""Plugin validation command."""

from __future__ import annotations

import importlib.metadata
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from phlo.cli.commands.plugin.utils import console
from phlo.logging import get_logger
from phlo.plugins import discover_plugins, validate_plugins

logger = get_logger(__name__)


class ContainerCheckError(RuntimeError):
    """Raised when generated container checks cannot complete."""


def _plugin_package(plugin: Any) -> str:
    """Resolve the installed distribution owning a discovered service plugin."""
    top_level = plugin.__class__.__module__.split(".", 1)[0]
    distributions = importlib.metadata.packages_distributions().get(top_level, [])
    return sorted(distributions)[0] if distributions else plugin.metadata.name


def _service_inventory() -> tuple[dict[str, str], list[str]]:
    """Return generated service-file owners and all currently installed service names."""
    owners: dict[str, str] = {}
    service_names: list[str] = []
    discovered = discover_plugins(plugin_type="service", auto_register=True)
    for plugin in discovered.get("service", []):
        service_definition = plugin.service_definition
        service_name = service_definition.get("name")
        if service_name:
            service_names.append(service_name)
        for file_spec in plugin.get_files():
            destination = file_spec.get("dest")
            if destination:
                owners[destination] = _plugin_package(plugin)
    return owners, list(dict.fromkeys(service_names))


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., Any],
    label: str,
) -> str | None:
    """Run one external command and return a failure detail, if any."""
    try:
        result = runner(command, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return f"{label} could not start: {exc}"
    if result.returncode:
        detail = (result.stderr or result.stdout or "no output").strip()
        return f"{label} failed with exit code {result.returncode}: {detail}"
    return None


def _run_checked_command(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., Any],
    label: str,
) -> None:
    """Run one required setup command and raise on failure."""
    failure = _run_command(command, cwd=cwd, runner=runner, label=label)
    if failure:
        raise ContainerCheckError(failure)


def check_generated_containers(
    *,
    project_parent: Path | None = None,
    service_files: dict[str, str] | None = None,
    service_names: list[str] | None = None,
    command_runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Generate a disposable user project and check only its generated files."""
    command_runner = command_runner or subprocess.run
    phlo = shutil.which("phlo")
    docker = shutil.which("docker")
    if not docker:
        raise ContainerCheckError("required tool 'docker' is not installed or not on PATH")

    if service_files is None:
        owners, discovered_service_names = _service_inventory()
    else:
        owners = service_files
        discovered_service_names = service_names or []
    with tempfile.TemporaryDirectory(prefix="phlo-container-check-", dir=project_parent) as raw:
        project = Path(raw)
        project.mkdir(exist_ok=True)
        init_command = (
            [phlo, "services", "init", "--no-dev"]
            if phlo
            else [sys.executable, "-m", "phlo.cli.main", "services", "init", "--no-dev"]
        )
        _run_checked_command(
            init_command,
            cwd=project,
            runner=command_runner,
            label="phlo services init",
        )
        if discovered_service_names:
            add_command = [phlo or sys.executable, "services", "add"]
            if not phlo:
                add_command = [sys.executable, "-m", "phlo.cli.main", "services", "add"]
            for service_name in discovered_service_names:
                add_command.extend(["--service", service_name])
            add_command.append("--no-start")
            _run_checked_command(
                add_command,
                cwd=project,
                runner=command_runner,
                label="phlo services add",
            )

        generated_root = project / ".phlo"
        dockerfiles = (
            sorted(path for path in generated_root.rglob("Dockerfile") if path.is_file())
            if generated_root.exists()
            else []
        )
        relative_dockerfiles = [str(path.relative_to(generated_root)) for path in dockerfiles]
        unowned = [relative for relative in relative_dockerfiles if relative not in owners]
        if unowned:
            raise ContainerCheckError(
                "generated Dockerfile(s) have no package owner: " + ", ".join(unowned)
            )
        dockerfile_owners = {
            relative: owners[relative] for relative in relative_dockerfiles if relative in owners
        }

        failures: list[dict[str, str]] = []
        if dockerfiles:
            for dockerfile in dockerfiles:
                relative = str(dockerfile.relative_to(generated_root))
                failure = _run_command(
                    [
                        docker,
                        "run",
                        "--rm",
                        "-v",
                        f"{project.resolve()}:/workspace:ro",
                        "hadolint/hadolint:latest",
                        "/bin/hadolint",
                        f"/workspace/.phlo/{relative}",
                    ],
                    cwd=project,
                    runner=command_runner,
                    label=f"hadolint {relative}",
                )
                if failure:
                    failures.append(
                        {
                            "tool": "hadolint",
                            "package": dockerfile_owners[relative],
                            "target": relative,
                            "detail": failure,
                        }
                    )

        trivy_failure = _run_command(
            [
                docker,
                "run",
                "--rm",
                "-v",
                f"{project.resolve()}:/workspace:ro",
                "aquasec/trivy:latest",
                "config",
                "--exit-code",
                "1",
                "--severity",
                "HIGH,CRITICAL",
                "/workspace/.phlo",
            ],
            cwd=project,
            runner=command_runner,
            label="trivy config",
        )
        if trivy_failure:
            failures.append(
                {
                    "tool": "trivy",
                    "package": "project",
                    "target": ".phlo",
                    "detail": trivy_failure,
                }
            )
        if failures:
            lines = ["Generated container checks failed:"]
            lines.extend(
                f"- {failure['tool']} [{failure['package']}] {failure['target']}: "
                f"{failure['detail']}"
                for failure in failures
            )
            raise ContainerCheckError("\n".join(lines))

    return {
        "dockerfiles": relative_dockerfiles,
        "owners": dockerfile_owners,
        "hadolint": "passed" if dockerfiles else "skipped (no generated Dockerfiles)",
        "trivy": "passed",
    }


@click.command(name="check")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
@click.option(
    "--containers",
    is_flag=True,
    help="Generate a temporary user project and check its generated container files.",
)
def check_cmd(output_json: bool, containers: bool):
    """Validate installed plugins.

    Checks that all plugins comply with their interface requirements
    and reports any issues.

    Examples:
        phlo plugin check           # Check all plugins
        phlo plugin check --json    # Output as JSON
        phlo plugin check --containers  # Check generated container files
    """
    try:
        if not output_json:
            console.print("Validating plugins...")

        # First discover plugins
        discover_plugins(auto_register=True)

        # Then validate
        validation_results = validate_plugins()

        if containers:
            validation_results["containers"] = check_generated_containers()

        if output_json:
            click.echo(json.dumps(validation_results, indent=2))
            return

        # Rich formatted output
        valid = validation_results.get("valid", [])
        invalid = validation_results.get("invalid", [])
        logger.info(
            "plugin_check_completed",
            valid_count=len(valid),
            invalid_count=len(invalid),
            output_json=output_json,
        )

        console.print(f"\n[green]✓ Valid Plugins: {len(valid)}[/green]")
        if valid:
            for plugin_id in valid:
                console.print(f"  [green]✓[/green] {plugin_id}")

        if invalid:
            logger.warning("plugin_check_validation_failed", invalid_count=len(invalid))
            console.print(f"\n[red]✗ Invalid Plugins: {len(invalid)}[/red]")
            for plugin_id in invalid:
                console.print(f"  [red]✗[/red] {plugin_id}")
            sys.exit(1)
        else:
            console.print("\n[green]All plugins are valid![/green]")
            if containers:
                checked = validation_results["containers"]
                console.print(
                    f"\n[green]Generated container checks passed:[/green] "
                    f"{len(checked['dockerfiles'])} Dockerfile(s)"
                )

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("plugin_check_failed", output_json=output_json)
        console.print(f"[red]Error validating plugins: {e}[/red]")
        sys.exit(1)
