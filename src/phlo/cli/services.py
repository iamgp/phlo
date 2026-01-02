"""
Phlo Services Management

Manages Docker infrastructure for Phlo projects.
Creates .phlo/ directory in user projects with docker-compose configuration.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Optional

import click
import yaml

from phlo.cli._services.command import CommandError, run_command
from phlo.cli._services.compose import compose_base_cmd
from phlo.cli._services.utils import (
    _resolve_container_name,
    find_dagster_container,
    get_project_config,
    get_project_name,
)
from phlo.discovery import ServiceDefinition

PHLO_CONFIG_FILE = "phlo.yaml"
NATIVE_STATE_FILE = "native-processes.json"

PHLO_CONFIG_TEMPLATE = """# Phlo Project Configuration
name: {name}
description: "{description}"

# Configure infrastructure overrides as needed. For example:
#
# infrastructure:
#   services:
#     postgres:
#       host: custom-host  # Override postgres host
#   container_naming_pattern: "{{project}}_{{service}}"  # Custom naming
#
# Non-secret environment defaults (committed):
#
# env:
#   POSTGRES_PORT: 10000
#   DAGSTER_PORT: 10006
#
# Secrets belong in .phlo/.env.local (not committed).
"""


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
                continue
            key, value = trimmed.split("=", 1)
            values[key] = value
    except OSError:
        return {}
    return values


def _get_env_overrides(config: dict) -> dict[str, object]:
    env_overrides = config.get("env", {})
    return env_overrides if isinstance(env_overrides, dict) else {}


def _warn_secret_env_overrides(
    env_overrides: dict[str, object], services: list[ServiceDefinition]
) -> None:
    if not env_overrides:
        return
    secret_keys = {
        name for service in services for name, cfg in service.env_vars.items() if cfg.get("secret")
    }
    overlapping = sorted(set(env_overrides).intersection(secret_keys))
    if overlapping:
        click.echo(
            "Warning: phlo.yaml env overrides include secret keys. "
            "Move these to .phlo/.env.local instead:",
            err=True,
        )
        click.echo(f"  {', '.join(overlapping)}", err=True)


def resolve_phlo_package_dir(path: Path) -> Path | None:
    """Resolve a path to the `src/phlo` package directory (must contain `__init__.py`).

    Accepts either:
    - the package directory itself (`.../src/phlo`)
    - a repo root containing `src/phlo`
    - a `src/` directory containing `phlo/`
    """
    candidates = [
        path,
        path / "src" / "phlo",
        path / "phlo",
    ]

    for candidate in candidates:
        if candidate.is_dir() and (candidate / "__init__.py").is_file():
            return candidate

    return None


def relpath_from_phlo_dir(path: Path) -> str:
    """Return a `.phlo/`-relative path string for docker-compose volume mounts."""
    try:
        return str(os.path.relpath(path, Path.cwd() / ".phlo"))
    except ValueError:
        # On Windows, relpath can fail across drives
        return str(path)


def detect_phlo_source_path() -> str | None:
    """Detect phlo source path using multiple strategies.

    Tries in order:
    1. PHLO_DEV_SOURCE environment variable
    2. Common directory patterns relative to CWD
    3. Returns None if not found

    Returns:
        Relative path to phlo source from .phlo/ directory, or None.
    """
    # Strategy 1: Environment variable
    env_path = os.environ.get("PHLO_DEV_SOURCE")
    if env_path:
        if resolved := resolve_phlo_package_dir(Path(env_path)):
            return relpath_from_phlo_dir(resolved)

    # Strategy 2: Common directory patterns
    candidates: list[Path] = []

    # Current working tree (handles running from the phlo repo itself)
    candidates.extend(
        [
            Path.cwd() / "src" / "phlo",
            Path.cwd(),
            Path.cwd() / "src",
        ]
    )

    # Sibling `phlo/` repo (common: `~/Developer/{phlo,project}`) - walk up a few levels.
    for parent in list(Path.cwd().parents)[:4]:
        candidates.append(parent / "phlo")

    for candidate in candidates:
        if resolved := resolve_phlo_package_dir(candidate):
            return relpath_from_phlo_dir(resolved)

    return None


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        run_command(["docker", "info"], timeout_seconds=10, check=True)
        return True
    except (CommandError, FileNotFoundError, TimeoutExpired, OSError):
        return False


def require_docker():
    """Exit with helpful message if Docker is not running."""
    if not check_docker_running():
        click.echo("Error: Docker is not running.", err=True)
        click.echo("", err=True)
        click.echo("Please start Docker Desktop and try again.", err=True)
        click.echo("Download: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)


# Re-export from utils for backwards compatibility
__all__ = ["get_project_config", "get_project_name", "find_dagster_container"]


def _normalize_hook_entries(hooks: object) -> list[dict[str, object]]:
    if hooks is None:
        return []
    if isinstance(hooks, list):
        entries: list[dict[str, object]] = []
        for item in hooks:
            if isinstance(item, dict):
                # Cast to proper type for type checker
                entries.append({str(k): v for k, v in item.items()})
            elif isinstance(item, list):
                entries.append({"command": item})
            elif isinstance(item, str):
                entries.append({"command": [item]})
        return entries
    if isinstance(hooks, dict):
        return [{str(k): v for k, v in hooks.items()}]
    return []


def _format_hook_command(command: object, substitutions: dict[str, str]) -> list[str]:
    if isinstance(command, str):
        command = [command]
    if not isinstance(command, list):
        return []
    formatted: list[str] = []
    for item in command:
        if not isinstance(item, str):
            continue
        formatted.append(item.format(**substitutions))
    return formatted


def _run_service_hooks(
    hook_name: str,
    service_names: list[str],
    project_name: str,
    project_root: Path,
) -> None:
    if not service_names:
        return

    from phlo.discovery import ServiceDiscovery

    discovery = ServiceDiscovery()
    for name in service_names:
        service = discovery.get_service(name)
        if not service:
            continue
        hook_entries = _normalize_hook_entries(service.hooks.get(hook_name))
        if not hook_entries:
            continue
        substitutions = {
            "project_name": project_name,
            "service_name": service.name,
            "container_name": _resolve_container_name(service.name, project_name),
            "project_root": str(project_root),
        }
        for hook in hook_entries:
            required_module = hook.get("requires")
            if isinstance(required_module, str):
                import importlib.util

                if importlib.util.find_spec(required_module) is None:
                    continue

            # Respect delay setting
            delay = hook.get("delay")
            if isinstance(delay, (int, float)) and delay > 0:
                import time

                time.sleep(delay)

            command = _format_hook_command(hook.get("command"), substitutions)
            if not command:
                continue

            # Use project's venv python if command starts with 'python'
            if command and command[0] in ("python", "python3"):
                venv_python = project_root / ".venv" / "bin" / "python"
                if venv_python.exists():
                    command[0] = str(venv_python)

            timeout = hook.get("timeout_seconds")
            if isinstance(timeout, str) and timeout.isdigit():
                timeout = int(timeout)
            elif not isinstance(timeout, int):
                timeout = None
            try:
                result = run_command(command, timeout_seconds=timeout, check=False)
            except (CommandError, TimeoutExpired, OSError) as exc:
                click.echo(
                    f"Warning: hook '{hook_name}' for {service.name} failed: {exc}",
                    err=True,
                )
                continue
            if result.returncode != 0:
                click.echo(
                    f"Warning: hook '{hook_name}' for {service.name} failed: {result.stderr}",
                    err=True,
                )


def _emit_service_lifecycle_events(
    phase: str,
    service_names: list[str],
    project_name: str,
    project_root: Path,
    *,
    status: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    if not service_names:
        return
    from phlo.hooks import ServiceLifecycleEventContext, ServiceLifecycleEventEmitter

    for name in service_names:
        emitter = ServiceLifecycleEventEmitter(
            ServiceLifecycleEventContext(
                service_name=name,
                project_name=project_name,
                project_root=str(project_root),
                container_name=_resolve_container_name(name, project_name),
            )
        )
        emitter.emit(phase=phase, status=status, metadata=metadata)


def get_phlo_dir() -> Path:
    """Get the .phlo directory path in current project."""
    return Path.cwd() / ".phlo"


def ensure_phlo_dir() -> Path:
    """Ensure .phlo directory exists with required files."""
    phlo_dir = get_phlo_dir()

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    return phlo_dir


def _native_state_path(project_root: Path) -> Path:
    return project_root / ".phlo" / NATIVE_STATE_FILE


def _load_native_state(project_root: Path) -> dict[str, dict]:
    path = _native_state_path(project_root)
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f) or {}
    except (json.JSONDecodeError, OSError) as e:
        click.echo(f"Warning: Failed to read native state file {path}: {e}", err=True)
        return {}


def _save_native_state(project_root: Path, state: dict[str, dict]) -> None:
    path = _native_state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(path)


def _stop_native_processes(project_root: Path, service_names: list[str] | None = None) -> None:
    state = _load_native_state(project_root)
    if not state:
        return

    target_names = service_names or list(state.keys())
    for name in target_names:
        entry = state.get(name)
        if not entry:
            continue
        pid = entry.get("pid")
        if not isinstance(pid, int):
            state.pop(name, None)
            continue

        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            state.pop(name, None)
            continue
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                state.pop(name, None)
                continue

        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                state.pop(name, None)
                break
            time.sleep(0.25)

    if state:
        _save_native_state(project_root, state)
    else:
        _native_state_path(project_root).unlink(missing_ok=True)


def get_profile_service_names(profile_names: tuple[str, ...]) -> list[str]:
    """Get service names for the specified profiles.

    Args:
        profile_names: Tuple of profile names (e.g., ('observability', 'api'))

    Returns:
        List of service names belonging to those profiles.
    """
    if not profile_names:
        return []

    from phlo.services import ServiceDiscovery

    discovery = ServiceDiscovery()
    service_names: list[str] = []

    for profile in profile_names:
        services = discovery.get_services_by_profile(profile)
        service_names.extend(s.name for s in services)

    return service_names


@click.group()
def services():
    """Manage Phlo infrastructure services (Docker)."""
    pass


@services.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--name", "project_name", help="Project name (default: directory name)")
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
@click.option(
    "--no-dev",
    is_flag=True,
    help="Explicitly disable dev mode (useful when regenerating without dev mounts)",
)
@click.option(
    "--phlo-source",
    type=click.Path(exists=True),
    help="Path to phlo repo root or `src/phlo` (default: auto-detect or PHLO_DEV_SOURCE env var)",
)
def init(
    force: bool,
    project_name: Optional[str],
    dev: bool,
    no_dev: bool,
    phlo_source: Optional[str],
):
    """Initialize Phlo infrastructure in .phlo/ directory.

    Creates complete Docker Compose configuration for the full Phlo stack:
    - PostgreSQL, MinIO, Nessie (storage layer)
    - Trino (query engine)
    - Dagster (orchestration)
    - Observatory (data platform UI)
    - Superset (BI)
    - pgweb (database admin)
    - Optional: Prometheus, Loki, Grafana (--profile observability)
    - Optional: PostgREST, Hasura (--profile api)

    Use --dev to mount local phlo source for development iteration.
    Use --no-dev to explicitly generate config without dev mounts.

    Examples:
        phlo services init
        phlo services init --name my-lakehouse
        phlo services init --force
        phlo services init --dev
        phlo services init --dev --phlo-source ../../src/phlo
        phlo services init --no-dev --force  # Regenerate without dev mode
    """
    from phlo.services import ComposeGenerator, ServiceDiscovery

    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if phlo_dir.exists() and not force:
        click.echo(f"Directory {phlo_dir} already exists.", err=True)
        click.echo("Use --force to overwrite.", err=True)
        sys.exit(1)

    # Handle conflicting flags
    if dev and no_dev:
        click.echo("Error: Cannot specify both --dev and --no-dev.", err=True)
        sys.exit(1)

    # --no-dev takes precedence
    if no_dev:
        dev = False

    # Auto-enable dev mode if we can detect a local Phlo checkout and the user didn't opt out.
    phlo_src_path: str | None = None
    if not dev and not no_dev and not phlo_source:
        if detected := detect_phlo_source_path():
            dev = True
            phlo_src_path = detected
            click.echo(f"Dev mode: auto-enabled (path: {phlo_src_path})")

    # Derive project name from directory if not specified
    if not project_name:
        project_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")

    # Auto-detect phlo source path for dev mode using flexible detection
    if dev:
        if phlo_src_path:
            # Already resolved (auto-enabled above)
            pass
        elif phlo_source:
            phlo_source_path = Path(phlo_source)
            if not phlo_source_path.is_absolute():
                phlo_source_path = (Path.cwd() / phlo_source_path).resolve()
            else:
                phlo_source_path = phlo_source_path.resolve()
            resolved_phlo_source = resolve_phlo_package_dir(phlo_source_path)
            if not resolved_phlo_source:
                click.echo(
                    "Error: --phlo-source must point to the phlo repo root or `src/phlo` package.",
                    err=True,
                )
                sys.exit(1)
            phlo_src_path = str(os.path.relpath(resolved_phlo_source, phlo_dir))
            click.echo(f"Dev mode: using phlo source at {resolved_phlo_source}")
        else:
            # Use flexible path detection
            phlo_src_path = detect_phlo_source_path()
            if phlo_src_path:
                click.echo(f"Dev mode: auto-detected phlo source (path: {phlo_src_path})")
            else:
                click.echo(
                    "Warning: --dev specified but could not auto-detect phlo source.", err=True
                )
                click.echo(
                    "Set PHLO_DEV_SOURCE env var or use --phlo-source to specify the path.",
                    err=True,
                )
                dev = False

    # Create phlo.yaml config file in project root (only if it doesn't exist)
    if not config_file.exists():
        config_content = PHLO_CONFIG_TEMPLATE.format(
            name=project_name,
            description=f"{project_name} data lakehouse",
        )
        config_file.write_text(config_content)
        click.echo(f"Created: {PHLO_CONFIG_FILE}")
    else:
        click.echo(f"Using existing: {PHLO_CONFIG_FILE}")

    # Create .phlo directory
    phlo_dir.mkdir(parents=True, exist_ok=True)

    # Discover services
    discovery = ServiceDiscovery()
    all_services = discovery.discover()

    if not all_services:
        click.echo(
            "Error: No services found. Install service plugins or check entry points.",
            err=True,
        )
        sys.exit(1)

    # Load existing phlo.yaml config for user overrides
    existing_config = {}
    if config_file.exists():
        with open(config_file) as f:
            existing_config = yaml.safe_load(f) or {}
    user_overrides = existing_config.get("services", {})
    env_overrides = _get_env_overrides(existing_config)

    # Collect disabled services (those with enabled: false)
    disabled_services = {
        name
        for name, cfg in user_overrides.items()
        if isinstance(cfg, dict) and cfg.get("enabled") is False
    }

    # Collect inline custom services (those with type: inline)
    from phlo.discovery import ServiceDefinition

    inline_services = [
        ServiceDefinition.from_inline(name, cfg)
        for name, cfg in user_overrides.items()
        if isinstance(cfg, dict) and cfg.get("type") == "inline"
    ]

    # Get default services (excluding disabled) + profile services + inline services
    default_services = discovery.get_default_services(disabled_services=disabled_services)
    profile_services = [
        s for s in all_services.values() if s.profile and s.name not in disabled_services
    ]
    services_to_install = default_services + profile_services + inline_services
    _warn_secret_env_overrides(env_overrides, services_to_install)

    # Generate docker-compose.yml
    composer = ComposeGenerator(discovery)
    compose_content = composer.generate_compose(
        services_to_install,
        phlo_dir,
        dev_mode=dev,
        phlo_src_path=phlo_src_path,
        user_overrides=user_overrides,
    )

    compose_file = phlo_dir / "docker-compose.yml"
    compose_file.write_text(compose_content)
    click.echo(f"Created: {compose_file.relative_to(Path.cwd())}")

    # Generate .env + .env.local
    env_file = phlo_dir / ".env"
    env_local_file = phlo_dir / ".env.local"
    existing_env_local = _parse_env_file(env_local_file)
    env_content = composer.generate_env(services_to_install, env_overrides=env_overrides)
    env_local_content = composer.generate_env_local(
        services_to_install,
        env_overrides=env_overrides,
        existing_values=existing_env_local,
    )
    env_file.write_text(env_content)
    click.echo(f"Created: {env_file.relative_to(Path.cwd())}")
    env_local_file.write_text(env_local_content)
    click.echo(f"Created: {env_local_file.relative_to(Path.cwd())}")

    # Generate .gitignore
    gitignore_file = phlo_dir / ".gitignore"
    gitignore_file.write_text(composer.generate_gitignore())
    click.echo(f"Created: {gitignore_file.relative_to(Path.cwd())}")

    # Create volumes directory
    volumes_dir = phlo_dir / "volumes"
    volumes_dir.mkdir(exist_ok=True)

    # Copy service files (Dockerfiles, configs, etc.)
    copied_files = composer.copy_service_files(services_to_install, phlo_dir)
    for f in copied_files:
        click.echo(f"Created: .phlo/{f}")

    # Summary
    click.echo("")
    click.echo("Phlo infrastructure initialized.")
    click.echo("")

    default_names = sorted([s.name for s in default_services])
    click.echo(f"Default services: {', '.join(default_names)}")

    profiles = discovery.get_available_profiles()
    if profiles:
        click.echo(f"Optional profiles: {', '.join(sorted(profiles))}")

    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Commit non-secret defaults in phlo.yaml (env:)")
    click.echo("  2. Set secrets in .phlo/.env.local")
    click.echo("  3. Run: phlo services start")
    click.echo("  4. Inspect services with: phlo services list")


@services.command("list")
@click.option("--all", "show_all", is_flag=True, help="Show all services including optional")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def list_services(show_all: bool, output_json: bool):
    """List available services with status and configuration.

    Examples:
        phlo services list
        phlo services list --all
        phlo services list --json
    """
    import json
    from pathlib import Path

    import yaml

    from phlo.cli._services.command import run_command
    from phlo.cli._services.utils import get_project_name
    from phlo.discovery import ServiceDefinition, ServiceDiscovery

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
            ["docker", "ps", "--filter", f"name={project_name}", "--format", "json"],
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


@services.command("start")
@click.option("-d", "--detach", is_flag=True, default=True, help="Run in background")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option(
    "--profile",
    multiple=True,
    help="Enable optional profiles (e.g., observability, api)",
)
@click.option(
    "--service",
    multiple=True,
    help="Start only specific service(s) (e.g., --service postgres,minio or --service postgres --service minio)",
)
@click.option(
    "--native",
    is_flag=True,
    help="Run services with a native dev command as subprocesses (e.g., phlo-api, Observatory)",
)
def start(
    detach: bool,
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    native: bool,
):
    """Start Phlo infrastructure services.

    Examples:
        phlo services start
        phlo services start --build
        phlo services start --profile observability
        phlo services start --service postgres
        phlo services start --native  # Run Observatory/phlo-api as subprocesses
    """
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    project_name = get_project_name()

    if not compose_file.exists():
        click.echo("Error: docker-compose.yml not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    # This prevents restarting already-running core services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Starting services: {', '.join(services_list)}...")
    elif native:
        click.echo(f"Starting {project_name} infrastructure (native dev services enabled)...")
    else:
        click.echo(f"Starting {project_name} infrastructure...")

    # If native dev services are enabled, start Docker services excluding native ones,
    # then start native processes for the excluded services.
    native_service_names: set[str] = set()
    if native:
        from phlo.discovery import ServiceDiscovery
        from phlo.services.native import NativeProcessManager

        discovery = ServiceDiscovery()
        project_root = Path.cwd()
        dev_manager = NativeProcessManager(
            project_root, log_dir=project_root / ".phlo" / "native-logs"
        )

        for _, svc in discovery.discover().items():
            if dev_manager.can_run_dev(svc):
                native_service_names.add(svc.name)

        if not native_service_names:
            click.echo("Warning: No services support native mode; starting Docker only.", err=True)
            native = False

    docker_services_list = services_list
    if native and not docker_services_list and not profile:
        try:
            compose_config = yaml.safe_load(compose_file.read_text()) or {}
        except OSError as e:
            raise click.ClickException(f"Failed to read {compose_file}: {e}") from e
        except yaml.YAMLError as e:
            raise click.ClickException(f"Failed to parse {compose_file}: {e}") from e
        compose_service_names = list((compose_config.get("services") or {}).keys())
        docker_services_list = [n for n in compose_service_names if n not in native_service_names]

    if native and docker_services_list:
        docker_services_list = [n for n in docker_services_list if n not in native_service_names]

    # If the user explicitly requested services and all of them are native-capable,
    # avoid running `docker compose up` with no service args (which would start the entire stack).
    skip_docker_compose = bool(native and services_list and not docker_services_list)

    docker_service_names: list[str] = []
    if not skip_docker_compose:
        if docker_services_list:
            docker_service_names = docker_services_list
        else:
            try:
                compose_config = yaml.safe_load(compose_file.read_text()) or {}
            except (OSError, yaml.YAMLError):
                compose_config = {}
            docker_service_names = list((compose_config.get("services") or {}).keys())
        _emit_service_lifecycle_events(
            "pre_start",
            docker_service_names,
            project_name=project_name,
            project_root=Path.cwd(),
            metadata={"native": False},
        )

    if not skip_docker_compose:
        require_docker()
    elif build:
        click.echo("Warning: --build ignored when starting native-only services.", err=True)

    def _stop_docker_services(service_names: set[str]) -> None:
        if not service_names:
            return
        stop_cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
        stop_cmd.append("stop")
        stop_cmd.extend(sorted(service_names))
        run_command(stop_cmd, check=False, capture_output=False)

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    cmd.append("up")

    if detach:
        cmd.append("-d")

    if build:
        cmd.append("--build")

    # Add specific services if specified
    if docker_services_list:
        cmd.extend(docker_services_list)

    try:
        if skip_docker_compose:
            # Skip docker-compose - create a successful result
            result = subprocess.CompletedProcess(args=[], returncode=0)
        else:
            result = run_command(cmd, check=False, capture_output=False)

        if result.returncode == 0:
            if native:
                import asyncio

                from phlo.discovery import ServiceDiscovery
                from phlo.services.native import NativeProcessManager

                discovery = ServiceDiscovery()
                project_root = Path.cwd()
                dev_manager = NativeProcessManager(
                    project_root, log_dir=project_root / ".phlo" / "native-logs"
                )

                available = {
                    svc.name: svc
                    for svc in discovery.discover().values()
                    if dev_manager.can_run_dev(svc)
                }

                if services_list:
                    requested = [available[n] for n in services_list if n in available]
                    expanded: dict[str, ServiceDefinition] = {svc.name: svc for svc in requested}
                    queue = list(requested)
                    while queue:
                        svc = queue.pop(0)
                        for dep_name in svc.depends_on:
                            dep = available.get(dep_name)
                            if dep and dep.name not in expanded:
                                expanded[dep.name] = dep
                                queue.append(dep)
                    native_to_start = discovery.resolve_dependencies(list(expanded.values()))
                else:
                    native_to_start = [available[n] for n in sorted(available)]

                # Avoid port collisions by ensuring any previously-started Docker containers for the
                # target native services are stopped before launching subprocesses.
                if not skip_docker_compose and native_to_start:
                    _stop_docker_services({svc.name for svc in native_to_start})

                # Avoid port collisions by stopping previously-started native processes for the
                # target services (do not stop unrelated native services).
                _stop_native_processes(project_root, [svc.name for svc in native_to_start])

                click.echo("")
                if native_to_start:
                    click.echo(
                        f"Starting native services: {', '.join(s.name for s in native_to_start)}..."
                    )
                else:
                    click.echo("No native services to start.")

                async def start_native_services():
                    started: dict[str, dict] = {}
                    env_overrides = {
                        "PHLO_PROJECT_PATH": str(project_root),
                        "ENV_FILE_PATH": str(project_root / ".phlo" / ".env"),
                    }
                    for svc in native_to_start:
                        _emit_service_lifecycle_events(
                            "pre_start",
                            [svc.name],
                            project_name=project_name,
                            project_root=project_root,
                            metadata={"native": True},
                        )
                        click.echo(f"  Starting {svc.name}...")
                        process = await dev_manager.start_service(svc, env_overrides=env_overrides)
                        if process:
                            click.echo(f"    ✓ {svc.name} started (pid {process.pid})")
                            started[svc.name] = {
                                "pid": process.pid,
                                "started_at": time.time(),
                                "log": str(
                                    project_root / ".phlo" / "native-logs" / f"{svc.name}.log"
                                ),
                            }
                            _emit_service_lifecycle_events(
                                "post_start",
                                [svc.name],
                                project_name=project_name,
                                project_root=project_root,
                                status="success",
                                metadata={"native": True, "pid": process.pid},
                            )
                        else:
                            click.echo(f"    ✗ {svc.name} failed to start", err=True)
                            _emit_service_lifecycle_events(
                                "post_start",
                                [svc.name],
                                project_name=project_name,
                                project_root=project_root,
                                status="failure",
                                metadata={"native": True},
                            )
                    return started

                started = asyncio.run(start_native_services())
                if started:
                    state = _load_native_state(project_root)
                    state.update(started)
                    _save_native_state(project_root, state)

                if skip_docker_compose:
                    click.echo("")
                    if native_to_start:
                        click.echo(
                            f"Native services started: {', '.join(s.name for s in native_to_start)}"
                        )
                    else:
                        click.echo("No native services started.")

                    if detach or not native_to_start:
                        return

                    def _stop_and_exit(_signum=None, _frame=None) -> None:
                        click.echo("\nStopping native services...")
                        _stop_native_processes(project_root, [svc.name for svc in native_to_start])
                        raise SystemExit(0)

                    old_sigterm = signal.signal(signal.SIGTERM, _stop_and_exit)
                    try:
                        click.echo("Press Ctrl+C to stop native services...")
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        _stop_and_exit()
                    finally:
                        signal.signal(signal.SIGTERM, old_sigterm)
                    return

            started_services: list[str] = []
            if not skip_docker_compose:
                try:
                    compose_config = yaml.safe_load(compose_file.read_text()) or {}
                except (OSError, yaml.YAMLError):
                    compose_config = {}
                compose_service_names = list((compose_config.get("services") or {}).keys())
                if docker_services_list:
                    started_services = [
                        name for name in docker_services_list if name in compose_service_names
                    ]
                else:
                    started_services = compose_service_names

            _emit_service_lifecycle_events(
                "post_start",
                started_services,
                project_name=project_name,
                project_root=Path.cwd(),
                status="success",
                metadata={"native": False},
            )
            _run_service_hooks(
                "post_start",
                started_services,
                project_name=project_name,
                project_root=Path.cwd(),
            )

            click.echo("")
            click.echo("Phlo infrastructure started.")
            if started_services:
                click.echo(f"Services running: {', '.join(sorted(started_services))}")
        else:
            _emit_service_lifecycle_events(
                "post_start",
                docker_service_names,
                project_name=project_name,
                project_root=Path.cwd(),
                status="failure",
                metadata={"native": False, "returncode": result.returncode},
            )
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        click.echo("Please install Docker: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("stop")
@click.option("-v", "--volumes", is_flag=True, help="Remove volumes (deletes data)")
@click.option(
    "--native",
    "stop_native",
    is_flag=True,
    help="Stop native dev services started with `phlo services start --native`",
)
@click.option(
    "--profile",
    multiple=True,
    help="Stop optional profile services",
)
@click.option(
    "--service",
    multiple=True,
    help="Stop only specific service(s) (e.g., --service postgres,minio or --service postgres --service minio)",
)
def stop(volumes: bool, stop_native: bool, profile: tuple[str, ...], service: tuple[str, ...]):
    """Stop Phlo infrastructure services.

    Examples:
        phlo services stop
        phlo services stop --volumes
        phlo services stop --profile observability
        phlo services stop --service postgres
        phlo services stop --service postgres,minio
    """
    project_root = Path.cwd()
    if stop_native:
        # Parse comma-separated services for native stop.
        native_services_list = []
        for s in service:
            native_services_list.extend(s.split(","))
        native_services_list = [s.strip() for s in native_services_list if s.strip()]
        native_targets = (
            native_services_list
            if native_services_list
            else list(_load_native_state(project_root).keys())
        )
        if native_targets:
            _emit_service_lifecycle_events(
                "pre_stop",
                native_targets,
                project_name=get_project_name(),
                project_root=project_root,
                metadata={"native": True},
            )
        _stop_native_processes(project_root, native_services_list or None)
        if native_targets:
            _emit_service_lifecycle_events(
                "post_stop",
                native_targets,
                project_name=get_project_name(),
                project_root=project_root,
                status="success",
                metadata={"native": True},
            )

    # If we only needed to stop native services, skip Docker.
    if stop_native and service and not volumes and not profile:
        click.echo("Stopped native services.")
        return

    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    # This prevents stopping all services when only profile services should be affected
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Stopping services: {', '.join(services_list)}...")
    else:
        click.echo(f"Stopping {project_name} infrastructure...")

    docker_targets = services_list
    if not docker_targets:
        try:
            compose_config = yaml.safe_load((phlo_dir / "docker-compose.yml").read_text()) or {}
        except (OSError, yaml.YAMLError):
            compose_config = {}
        docker_targets = list((compose_config.get("services") or {}).keys())
    if docker_targets:
        _emit_service_lifecycle_events(
            "pre_stop",
            docker_targets,
            project_name=project_name,
            project_root=project_root,
            metadata={"native": False},
        )

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)

    if services_list:
        # Stop specific services only
        cmd.extend(["stop", *services_list])
    else:
        # Stop all services
        cmd.append("down")
        if volumes:
            cmd.append("-v")
            click.echo("Warning: Removing volumes will delete all data.")

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            if docker_targets:
                _emit_service_lifecycle_events(
                    "post_stop",
                    docker_targets,
                    project_name=project_name,
                    project_root=project_root,
                    status="success",
                    metadata={"native": False},
                )
            if services_list:
                click.echo(f"Stopped services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure stopped.")
        else:
            if docker_targets:
                _emit_service_lifecycle_events(
                    "post_stop",
                    docker_targets,
                    project_name=project_name,
                    project_root=project_root,
                    status="failure",
                    metadata={"native": False, "returncode": result.returncode},
                )
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("reset")
@click.option(
    "--service",
    multiple=True,
    help="Reset only specific service(s) volumes (e.g., --service postgres,minio or --service postgres --service minio)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reset(service: tuple[str, ...], yes: bool):
    """Reset Phlo infrastructure by stopping services and deleting volumes.

    This stops all services and removes their data volumes for a clean slate.
    Use --service to selectively reset only specific service volumes.

    Examples:
        phlo services reset                      # Reset everything
        phlo services reset --service postgres   # Reset only postgres
        phlo services reset --service postgres,minio  # Reset multiple
        phlo services reset -y                   # Skip confirmation
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    compose_file = phlo_dir / "docker-compose.yml"
    project_name = get_project_name()
    volumes_dir = phlo_dir / "volumes"

    if not compose_file.exists():
        click.echo("Error: docker-compose.yml not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
        sys.exit(1)

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # Determine what to reset
    if services_list:
        target = f"services: {', '.join(services_list)}"
        volume_dirs = [volumes_dir / s for s in services_list]
    else:
        target = "all services"
        volume_dirs = [volumes_dir] if volumes_dir.exists() else []

    # Confirm
    if not yes:
        click.echo(f"This will stop {target} and DELETE their data volumes.")
        if not click.confirm("Are you sure you want to continue?"):
            click.echo("Aborted.")
            return

    # Stop services - selective or all
    if services_list:
        # Stop and remove only specific services
        click.echo(f"Stopping services: {', '.join(services_list)}...")
        cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
        cmd.extend(
            [
                "rm",
                "-f",  # Force removal
                "-s",  # Stop containers if running
                "-v",  # Remove anonymous volumes
                *services_list,  # Specific services
            ]
        )
    else:
        # Stop all services
        click.echo(f"Stopping {project_name} infrastructure...")
        cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
        cmd.extend(
            [
                "down",
                "-v",  # Remove Docker volumes
            ]
        )

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo(
                f"Warning: docker compose command failed with code {result.returncode}", err=True
            )
            click.echo(f"Command: {' '.join(cmd)}", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Warning: docker compose command timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)

    # Delete local volume directories
    deleted_count = 0
    for vol_dir in volume_dirs:
        if vol_dir.exists():
            try:
                if vol_dir.is_dir():
                    shutil.rmtree(vol_dir)
                    deleted_count += 1
                    click.echo(f"Deleted: {vol_dir.relative_to(phlo_dir)}")
            except OSError as e:
                click.echo(f"Warning: Could not delete {vol_dir}: {e}", err=True)

    # Recreate volumes directory if we deleted it entirely
    if not services_list and not volumes_dir.exists():
        volumes_dir.mkdir(parents=True, exist_ok=True)

    click.echo("")
    if services_list:
        click.echo(f"Reset complete for: {', '.join(services_list)}")
    else:
        click.echo("Full reset complete. All data volumes have been deleted.")
    click.echo("Run 'phlo services start' to start fresh.")


@services.command("restart")
@click.option("--build", is_flag=True, help="Build images before starting")
@click.option(
    "--profile",
    multiple=True,
    help="Restart optional profile services (e.g., observability, api)",
)
@click.option(
    "--service",
    multiple=True,
    help="Restart only specific service(s) (e.g., --service postgres,minio)",
)
@click.option(
    "--dev",
    is_flag=True,
    help="Development mode: mount local phlo source for instant iteration",
)
def restart(
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    dev: bool,
):
    """Restart Phlo infrastructure services (stop + start).

    Combines stop and start in a single command for convenience.

    Examples:
        phlo services restart                          # Restart all services
        phlo services restart --profile observability  # Restart profile services only
        phlo services restart --service postgres       # Restart specific service
        phlo services restart --build                  # Rebuild before starting
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    # Parse comma-separated services
    services_list = []
    for s in service:
        services_list.extend(s.split(","))
    services_list = [s.strip() for s in services_list if s.strip()]

    # When --profile is specified without --service, target only profile services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)

    if services_list:
        click.echo(f"Restarting services: {', '.join(services_list)}...")
    else:
        click.echo(f"Restarting {project_name} infrastructure...")

    # Stop services
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    if services_list:
        cmd.extend(["stop", *services_list])
    else:
        cmd.append("down")

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo(f"Warning: stop failed with code {result.returncode}", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Warning: stop timed out.", err=True)

    # Start services
    click.echo("")
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name, profiles=profile)
    cmd.extend(["up", "-d"])

    if build:
        cmd.append("--build")

    if services_list:
        cmd.extend(services_list)

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            click.echo("")
            if services_list:
                click.echo(f"Restarted services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure restarted.")
        else:
            click.echo(f"Error: start failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("status")
def status():
    """Show status of Phlo infrastructure services.

    Examples:
        phlo services status
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"])

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            click.echo("No services running or error checking status.", err=True)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)


@services.command("add")
@click.argument("service_name")
@click.option("--no-start", is_flag=True, help="Don't start the service after adding")
def add_service(service_name: str, no_start: bool):
    """Add an optional service to the project.

    Examples:
        phlo services add prometheus
        phlo services add grafana --no-start
        phlo services add hasura
    """
    from phlo.services import ServiceDiscovery

    phlo_dir = get_phlo_dir()
    config_file = Path.cwd() / PHLO_CONFIG_FILE

    if not phlo_dir.exists():
        click.echo("Error: .phlo directory not found.", err=True)
        click.echo("Run 'phlo services init' first.", err=True)
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
        click.echo("")
        click.echo("Available services:")
        for name in sorted(all_services.keys()):
            svc = all_services[name]
            marker = "[optional]" if svc.profile or not svc.default else "[default]"
            click.echo(f"  {name} {marker}")
        sys.exit(1)

    service = all_services[service_name]

    # Update config
    if "services" not in config:
        config["services"] = {}
    if "enabled" not in config["services"]:
        config["services"]["enabled"] = []

    enabled = config["services"]["enabled"]
    if service_name in enabled:
        click.echo(f"Service '{service_name}' is already enabled.")
        return

    enabled.append(service_name)
    config["services"]["enabled"] = sorted(set(enabled))

    # Write updated config
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    click.echo(f"Added '{service_name}' to phlo.yaml")

    # Regenerate docker-compose.yml
    _regenerate_compose(discovery, config, phlo_dir)

    click.echo(f"Service '{service_name}' added.")

    if not no_start:
        click.echo("")
        click.echo(f"Starting {service_name}...")
        project_name = get_project_name()

        cmd = compose_base_cmd(
            phlo_dir=phlo_dir,
            project_name=project_name,
            profiles=() if not service.profile else (service.profile,),
        )
        cmd.extend(["up", "-d", service_name])
        try:
            result = run_command(cmd, check=False, capture_output=False)
            if result.returncode == 0:
                click.echo(f"Service '{service_name}' started.")
            else:
                click.echo(f"Warning: Could not start {service_name}.", err=True)
                click.echo(f"Command: {' '.join(cmd)}", err=True)
        except (FileNotFoundError, TimeoutExpired, OSError) as e:
            click.echo(f"Warning: Could not start {service_name}: {e}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)


@services.command("remove")
@click.argument("service_name")
@click.option("--keep-running", is_flag=True, help="Don't stop the service")
def remove_service(service_name: str, keep_running: bool):
    """Remove a service from the project.

    This removes the service from your configuration.

    Examples:
        phlo services remove prometheus
        phlo services remove grafana --keep-running
    """
    from phlo.services import ServiceDiscovery

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
    if "services" not in config:
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


def _regenerate_compose(discovery, config: dict, phlo_dir: Path):
    """Regenerate docker-compose.yml based on current config."""
    from phlo.cli._services.selection import select_services_to_install
    from phlo.services import ComposeGenerator

    all_services = discovery.discover()

    # Get default services
    default_services = discovery.get_default_services()

    # Get enabled services from config
    enabled_names = config.get("services", {}).get("enabled", [])
    disabled_names = config.get("services", {}).get("disabled", [])

    services_to_install = select_services_to_install(
        all_services=all_services,
        default_services=default_services,
        enabled_names=enabled_names,
        disabled_names=disabled_names,
    )

    # Get user service overrides from config
    user_overrides = config.get("services", {})
    env_overrides = _get_env_overrides(config)

    # Generate docker-compose.yml
    composer = ComposeGenerator(discovery)
    compose_content = composer.generate_compose(
        services_to_install, phlo_dir, user_overrides=user_overrides
    )

    compose_file = phlo_dir / "docker-compose.yml"
    compose_file.write_text(compose_content)
    click.echo("Updated: .phlo/docker-compose.yml")

    _warn_secret_env_overrides(env_overrides, services_to_install)

    # Regenerate .env + .env.local
    env_file = phlo_dir / ".env"
    env_local_file = phlo_dir / ".env.local"
    existing_env_local = _parse_env_file(env_local_file)
    env_content = composer.generate_env(services_to_install, env_overrides=env_overrides)
    env_local_content = composer.generate_env_local(
        services_to_install,
        env_overrides=env_overrides,
        existing_values=existing_env_local,
    )
    env_file.write_text(env_content)
    click.echo("Updated: .phlo/.env")
    env_local_file.write_text(env_local_content)
    click.echo("Updated: .phlo/.env.local")

    # Copy any new service files
    copied_files = composer.copy_service_files(services_to_install, phlo_dir)
    for f in copied_files:
        click.echo(f"Updated: .phlo/{f}")


@services.command("logs")
@click.argument("service", required=False)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
@click.option("-n", "--tail", default=100, help="Number of lines to show")
def logs(service: Optional[str], follow: bool, tail: int):
    """View logs from Phlo infrastructure services.

    Examples:
        phlo services logs
        phlo services logs dagster
        phlo services logs -f
    """
    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(["logs", "--tail", str(tail)])

    if follow:
        cmd.append("-f")

    if service:
        cmd.append(service)

    try:
        run_command(cmd, check=False, capture_output=False)
    except FileNotFoundError:
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        click.echo("Error: docker logs timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
