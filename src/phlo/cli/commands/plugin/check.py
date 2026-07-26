"""Plugin validation command."""

from __future__ import annotations

import importlib.metadata
import json
import os
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
from phlo.plugins.discovery import ServiceDiscovery
from phlo.plugins.discovery._service_loading import resolve_plugin_source_path

logger = get_logger(__name__)

HADOLINT_IMAGE = (
    "hadolint/hadolint@sha256:27086352fd5e1907ea2b934eb1023f217c5ae087992eb59fde121dce9c9ff21e"
)
TRIVY_IMAGE = (
    "aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f"
)
MAX_TOOL_OUTPUT_CHARS = 64 * 1024
MAX_COMPOSE_CONFIG_CHARS = 4 * 1024 * 1024
_REAL_SUBPROCESS_RUN = subprocess.run


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
    package_roots: dict[Path, str] = {}
    discovered = discover_plugins(plugin_type="service", auto_register=True)
    for plugin in discovered.get("service", []):
        package = _plugin_package(plugin)
        source_path = resolve_plugin_source_path(plugin)
        if source_path:
            package_roots[source_path.resolve()] = package
        service_definition = plugin.service_definition
        service_name = service_definition.get("name")
        if service_name:
            service_names.append(service_name)
        for file_spec in plugin.get_files():
            destination = file_spec.get("dest")
            if destination:
                owners[destination] = package
    for service_name, definition in ServiceDiscovery().discover().items():
        source_path = definition.source_path
        if not source_path:
            continue
        resolved_source = source_path.resolve()
        matching_roots = [
            (len(root.parts), package)
            for root, package in package_roots.items()
            if resolved_source == root or root in resolved_source.parents
        ]
        if matching_roots:
            package = max(matching_roots)[1]
            owners.setdefault(f"@service:{service_name}", package)
            for file_spec in definition.files:
                destination = file_spec.get("dest")
                if destination:
                    owners.setdefault(destination, package)
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
        result = _run_with_capture(command, cwd=cwd, runner=runner)
    except OSError as exc:
        return f"{label} could not start: {exc}"
    if result.returncode:
        return _run_command_result_failure(result, label)
    return None


def _run_output_command(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., Any],
    label: str,
    max_output_chars: int = MAX_TOOL_OUTPUT_CHARS,
) -> tuple[str, str]:
    """Run a command and return stdout, raising with both output streams on failure."""
    try:
        result = _run_with_capture(
            command,
            cwd=cwd,
            runner=runner,
            max_output_chars=max_output_chars,
        )
    except OSError as exc:
        raise ContainerCheckError(f"{label} could not start: {exc}") from exc
    if result.returncode:
        failure = _run_command_result_failure(result, label)
        raise ContainerCheckError(failure)
    return result.stdout or "", result.stderr or ""


def _run_command_result_failure(result: Any, label: str) -> str:
    """Format a failed command result without losing either output stream."""
    output = []
    if result.stdout:
        output.append(f"stdout: {_limit_tool_output(result.stdout).strip()}")
    if result.stderr:
        output.append(f"stderr: {_limit_tool_output(result.stderr).strip()}")
    detail = "\n".join(output) or "no output"
    return f"{label} failed with exit code {result.returncode}: {detail}"


def _join_failure_details(*details: str | None) -> str:
    """Keep the context from multiple failed steps in the final report."""
    return "\n".join(detail for detail in details if detail) or "no output"


def _parse_vulnerability_waivers(values: tuple[str, ...]) -> dict[tuple[str, str], str]:
    """Parse explicit SERVICE=IMAGE=REASON vulnerability waivers."""
    waivers: dict[tuple[str, str], str] = {}
    for value in values:
        parts = [part.strip() for part in value.split("=", 2)]
        if len(parts) != 3 or not all(parts):
            raise click.BadParameter(
                "expected SERVICE=IMAGE=REASON",
                param_hint="--allow-vulnerable-image",
            )
        service, image, reason = parts
        key = (service, image)
        if key in waivers:
            raise click.BadParameter(
                f"duplicate waiver for {service} using {image}",
                param_hint="--allow-vulnerable-image",
            )
        waivers[key] = reason
    return waivers


def _run_with_capture(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., Any],
    max_output_chars: int = MAX_TOOL_OUTPUT_CHARS,
) -> Any:
    """Run a real command without retaining an unbounded scanner transcript."""
    if runner is _REAL_SUBPROCESS_RUN:
        return _run_bounded_subprocess(
            command,
            cwd=cwd,
            max_output_chars=max_output_chars,
        )
    return runner(command, cwd=cwd, capture_output=True, text=True, check=False)


def _run_bounded_subprocess(
    command: list[str],
    *,
    cwd: Path,
    max_output_chars: int = MAX_TOOL_OUTPUT_CHARS,
) -> subprocess.CompletedProcess[str]:
    """Run a command through spooled files and retain useful output at bounded size."""
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        completed = _REAL_SUBPROCESS_RUN(
            command,
            cwd=cwd,
            stdout=stdout_file,
            stderr=stderr_file,
            check=False,
        )
        return subprocess.CompletedProcess(
            command,
            completed.returncode,
            stdout=_read_bounded_file(stdout_file, max_output_chars=max_output_chars),
            stderr=_read_bounded_file(stderr_file, max_output_chars=max_output_chars),
        )


def _read_bounded_file(file_handle: Any, *, max_output_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    """Read a file's head and tail without loading a large tool report."""
    file_handle.seek(0, 2)
    size = file_handle.tell()
    if size <= max_output_chars:
        file_handle.seek(0)
        return file_handle.read().decode("utf-8", errors="replace")

    half_limit = max_output_chars // 2
    file_handle.seek(0)
    head = file_handle.read(half_limit)
    file_handle.seek(-half_limit, 2)
    tail = file_handle.read(half_limit)
    return (
        head.decode("utf-8", errors="replace")
        + f"\n... [output truncated; {size} bytes total] ...\n"
        + tail.decode("utf-8", errors="replace")
    )


def _limit_tool_output(value: str) -> str:
    """Bound output from injected runners as well as real subprocesses."""
    if len(value) <= MAX_TOOL_OUTPUT_CHARS:
        return value
    half_limit = MAX_TOOL_OUTPUT_CHARS // 2
    return (
        value[:half_limit]
        + f"\n... [output truncated; {len(value)} characters total] ...\n"
        + value[-half_limit:]
    )


def _trivy_vulnerability_evidence(stdout: str) -> dict[str, Any] | None:
    """Extract exact HIGH/CRITICAL findings from Trivy JSON output."""
    if not stdout.strip():
        return None
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    vulnerable_components: list[dict[str, str]] = []
    for result in report.get("Results") or []:
        for finding in result.get("Vulnerabilities") or []:
            severity = str(finding.get("Severity") or "").upper()
            if severity not in {"HIGH", "CRITICAL"}:
                continue
            vulnerable_components.append(
                {
                    "target": str(result.get("Target") or ""),
                    "class": str(result.get("Class") or ""),
                    "type": str(result.get("Type") or ""),
                    "component": str(finding.get("PkgName") or ""),
                    "installed_version": str(finding.get("InstalledVersion") or ""),
                    "fixed_version": str(finding.get("FixedVersion") or ""),
                    "vulnerability_id": str(finding.get("VulnerabilityID") or ""),
                    "severity": severity,
                }
            )
    return {
        "high_count": sum(finding["severity"] == "HIGH" for finding in vulnerable_components),
        "critical_count": sum(
            finding["severity"] == "CRITICAL" for finding in vulnerable_components
        ),
        "vulnerable_components": vulnerable_components,
    }


def _run_trivy_image_scan(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., Any],
    label: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Run Trivy once, preserving failure streams and returning structured findings."""
    try:
        result = _run_with_capture(command, cwd=cwd, runner=runner)
    except OSError as exc:
        return f"{label} could not start: {exc}", None

    evidence = _trivy_vulnerability_evidence(result.stdout or "")
    if result.returncode:
        return _run_command_result_failure(result, label), evidence
    return None, evidence or {
        "high_count": 0,
        "critical_count": 0,
        "vulnerable_components": [],
    }


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
    vulnerability_waivers: dict[tuple[str, str], str] | None = None,
    command_runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Generate a disposable user project and check only its generated files."""
    command_runner = command_runner or subprocess.run
    vulnerability_waivers = vulnerability_waivers or {}
    phlo = shutil.which("phlo")
    docker = shutil.which("docker")
    if not phlo:
        raise ContainerCheckError("required installed CLI 'phlo' is not installed or not on PATH")
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
        configured_trivy_cache = os.environ.get("PHLO_TRIVY_CACHE_DIR")
        trivy_cache = (
            Path(configured_trivy_cache).expanduser().resolve()
            if configured_trivy_cache
            else project / ".trivy-cache"
        )
        trivy_cache.mkdir(parents=True, exist_ok=True)
        init_command = [phlo, "services", "init", "--no-dev", "--force"]
        _run_checked_command(
            init_command,
            cwd=project,
            runner=command_runner,
            label="phlo services init",
        )
        if discovered_service_names:
            add_command = [phlo, "services", "add"]
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
                        HADOLINT_IMAGE,
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

        compose_file = generated_root / "docker-compose.yml"
        compose_command = [
            docker,
            "compose",
            "--profile",
            "*",
            "-f",
            str(compose_file),
            "--project-directory",
            str(generated_root),
            "config",
            "--format",
            "json",
        ]
        compose_stdout, _ = _run_output_command(
            compose_command,
            cwd=project,
            runner=command_runner,
            label="docker compose config",
            max_output_chars=MAX_COMPOSE_CONFIG_CHARS,
        )
        try:
            compose_config = json.loads(compose_stdout)
            compose_services = compose_config["services"]
            compose_project = compose_config["name"]
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise ContainerCheckError(
                "docker compose config returned invalid service JSON"
            ) from exc

        service_owners = {
            name.removeprefix("@service:"): package
            for name, package in owners.items()
            if name.startswith("@service:")
        }
        service_results: list[dict[str, Any]] = []
        image_ids: dict[str, str] = {}
        resolved_image_ids: dict[str, str] = {}
        for service_name, service in compose_services.items():
            package = service_owners.get(service_name)
            if not package:
                raise ContainerCheckError(
                    f"generated Compose service '{service_name}' has no package owner"
                )
            image = service.get("image")
            locally_built = bool(service.get("build"))
            build_failure: str | None = None
            if locally_built:
                build_failure = _run_command(
                    [
                        docker,
                        "compose",
                        "--profile",
                        "*",
                        "-f",
                        str(compose_file),
                        "--project-directory",
                        str(generated_root),
                        "build",
                        "--quiet",
                        service_name,
                    ],
                    cwd=project,
                    runner=command_runner,
                    label=f"docker compose build {service_name}",
                )
                image = image or f"{compose_project}-{service_name}"
            elif not image:
                service_results.append(
                    {
                        "service": service_name,
                        "package": package,
                        "image": "",
                        "status": "failed",
                        "image_scan": "unavailable",
                        "detail": "generated service has neither image nor build",
                    }
                )
                continue
            image_id = resolved_image_ids.get(image)
            if image_id is None:
                pull_failure = None
                if not locally_built or build_failure:
                    pull_failure = _run_command(
                        [docker, "pull", image],
                        cwd=project,
                        runner=command_runner,
                        label=f"docker pull {service_name}",
                    )
                if pull_failure:
                    service_results.append(
                        {
                            "service": service_name,
                            "package": package,
                            "image": image,
                            "status": "failed",
                            "image_scan": "unavailable",
                            "detail": _join_failure_details(build_failure, pull_failure),
                        }
                    )
                    continue
                try:
                    inspect_stdout, _ = _run_output_command(
                        [docker, "image", "inspect", "--format", "{{.Id}}", image],
                        cwd=project,
                        runner=command_runner,
                        label=f"docker image inspect {service_name}",
                    )
                except ContainerCheckError as exc:
                    service_results.append(
                        {
                            "service": service_name,
                            "package": package,
                            "image": image,
                            "status": "failed",
                            "image_scan": "unavailable",
                            "detail": _join_failure_details(build_failure, str(exc)),
                        }
                    )
                    continue
                image_id = inspect_stdout.strip()
            if not image_id:
                service_results.append(
                    {
                        "service": service_name,
                        "package": package,
                        "image": image,
                        "status": "failed",
                        "image_scan": "unavailable",
                        "detail": _join_failure_details(
                            build_failure, "docker image inspect returned no image ID"
                        ),
                    }
                )
                continue
            resolved_image_ids[image] = image_id
            image_ids[service_name] = image_id
            service_results.append(
                {
                    "service": service_name,
                    "package": package,
                    "image": image,
                    "image_id": image_id,
                    "status": "failed" if build_failure else "pending",
                    "image_scan": "pending",
                    **({"detail": build_failure} if build_failure else {}),
                }
            )

        for image_id in dict.fromkeys(image_ids.values()):
            image_services = [name for name, value in image_ids.items() if value == image_id]
            trivy_image_failure, vulnerability_evidence = _run_trivy_image_scan(
                [
                    docker,
                    "run",
                    "--rm",
                    "-v",
                    "/var/run/docker.sock:/var/run/docker.sock",
                    "-v",
                    f"{trivy_cache.resolve()}:/root/.cache/trivy",
                    TRIVY_IMAGE,
                    "image",
                    "--timeout",
                    "15m",
                    "--exit-code",
                    "1",
                    "--scanners",
                    "vuln",
                    "--severity",
                    "HIGH,CRITICAL",
                    "--format",
                    "json",
                    image_id,
                ],
                cwd=project,
                runner=command_runner,
                label=f"trivy image {image_id}",
            )
            for result in service_results:
                if result.get("service") in image_services:
                    if vulnerability_evidence is not None:
                        result.update(vulnerability_evidence)
                    waiver = vulnerability_waivers.get((result["service"], result["image"]))
                    build_failed = result["status"] == "failed"
                    if trivy_image_failure and waiver and vulnerability_evidence is not None:
                        result["image_scan"] = "waived"
                        result["vulnerability_waiver"] = waiver
                        result["detail"] = _join_failure_details(
                            result.get("detail"), trivy_image_failure
                        )
                        result["status"] = "failed" if build_failed else "waived"
                        continue
                    result["status"] = "failed" if trivy_image_failure or build_failed else "passed"
                    result["image_scan"] = "failed" if trivy_image_failure else "passed"
                    if trivy_image_failure:
                        result["detail"] = _join_failure_details(
                            result.get("detail"), trivy_image_failure
                        )

        trivy_failure = _run_command(
            [
                docker,
                "run",
                "--rm",
                "-v",
                f"{project.resolve()}:/workspace:ro",
                "-v",
                f"{trivy_cache.resolve()}:/root/.cache/trivy",
                TRIVY_IMAGE,
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
        reported_image_failures: set[str] = set()
        for result in service_results:
            if result["status"] in {"passed", "waived"}:
                continue
            failure_key = result.get("image_id", result["service"])
            if failure_key in reported_image_failures:
                continue
            reported_image_failures.add(failure_key)
            failures.append(
                {
                    "tool": "trivy image",
                    "package": result["package"],
                    "target": result["service"],
                    "detail": result.get("detail", "image scan failed"),
                }
            )
        missing_results = [
            result["service"]
            for result in service_results
            if result.get("image_scan") not in {"passed", "failed", "unavailable", "waived"}
        ]
        if missing_results:
            failures.append(
                {
                    "tool": "trivy image",
                    "package": "unknown",
                    "target": ", ".join(missing_results),
                    "detail": "generated service has no image-scan result",
                }
            )
        if failures:
            lines = ["Generated container checks failed:"]
            lines.extend(
                f"- service [{result['package']}] {result['service']}: "
                f"{result['image'] or '<no image>'} -> {result['status']} "
                f"(image scan: {result.get('image_scan', 'missing')})"
                for result in service_results
            )
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
        "trivy": (
            "passed with explicit vulnerability waiver(s)"
            if any(result.get("image_scan") == "waived" for result in service_results)
            else "passed"
        ),
        "services": service_results,
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
@click.option(
    "--allow-vulnerable-image",
    "vulnerability_waiver_values",
    multiple=True,
    metavar="SERVICE=IMAGE=REASON",
    help="Explicitly waive HIGH/CRITICAL findings for one exact generated service image.",
)
def check_cmd(
    output_json: bool,
    containers: bool,
    vulnerability_waiver_values: tuple[str, ...],
):
    """Validate installed plugins.

    Checks that all plugins comply with their interface requirements
    and reports any issues.

    Examples:
        phlo plugin check           # Check all plugins
        phlo plugin check --json    # Output as JSON
        phlo plugin check --containers  # Check generated container files
        phlo plugin check --containers --allow-vulnerable-image SERVICE=IMAGE=REASON
    """
    try:
        if not output_json:
            console.print("Validating plugins...")

        # First discover plugins
        discover_plugins(auto_register=True)

        # Then validate
        validation_results = validate_plugins()

        if containers:
            validation_results["containers"] = check_generated_containers(
                vulnerability_waivers=_parse_vulnerability_waivers(vulnerability_waiver_values)
            )

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
                for service in checked["services"]:
                    if service["status"] == "waived":
                        console.print(
                            f"  [yellow]⚠ WAIVED[/yellow] {service['package']} / "
                            f"{service['service']} → {service['image']}: "
                            f"{service['vulnerability_waiver']}"
                        )
                        console.print(f"    [yellow]{service['detail']}[/yellow]")
                        continue
                    console.print(
                        f"  [green]✓[/green] {service['package']} / {service['service']} "
                        f"→ {service['image']} ({service['status']})"
                    )

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("plugin_check_failed", output_json=output_json)
        console.print(f"Error validating plugins: {e}", style="red", markup=False)
        sys.exit(1)
