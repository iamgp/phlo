"""Shared utilities for services commands."""

import json
import os
import signal
import sys
import time
from pathlib import Path

import click

from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.utils import _resolve_container_name

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


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        run_command(["docker", "info"], timeout_seconds=10, check=True)
        return True
    except Exception:
        return False


def require_docker():
    """Exit with helpful message if Docker is not running."""
    if not check_docker_running():
        click.echo("Error: Docker is not running.", err=True)
        click.echo("", err=True)
        click.echo("Please start Docker Desktop and try again.", err=True)
        click.echo("Download: https://docs.docker.com/get-docker/", err=True)
        sys.exit(1)


def resolve_phlo_package_dir(path: Path) -> Path | None:
    """Resolve a path to the `src/phlo` package directory (must contain `__init__.py`).

    Accepts either:
    - the package directory itself (`.../src/phlo`)
    - a repo root containing `src/phlo`
    - a `src/` directory containing `phlo/`
    """
    candidates = (path, path / "src" / "phlo", path / "phlo")
    return next(
        (c for c in candidates if c.is_dir() and (c / "__init__.py").is_file()),
        None,
    )


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


def _get_env_overrides(config: dict) -> dict[str, object]:
    env_overrides = config.get("env", {})
    return env_overrides if isinstance(env_overrides, dict) else {}


def _warn_secret_env_overrides(env_overrides: dict[str, object], services: list) -> None:
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


def _normalize_hook_entries(hooks: object) -> list[dict[str, object]]:
    if hooks is None:
        return []
    if isinstance(hooks, dict):
        return [{str(k): v for k, v in hooks.items()}]
    if not isinstance(hooks, list):
        return []
    entries: list[dict[str, object]] = []
    for item in hooks:
        if isinstance(item, dict):
            entries.append({str(k): v for k, v in item.items()})
        elif isinstance(item, list):
            entries.append({"command": item})
        elif isinstance(item, str):
            entries.append({"command": [item]})
    return entries


def _format_hook_command(command: object, substitutions: dict[str, str]) -> list[str]:
    if isinstance(command, str):
        command = [command]
    if not isinstance(command, list):
        return []

    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return ""

    formatted: list[str] = []
    for item in command:
        if not isinstance(item, str):
            continue
        formatted.append(item.format_map(_SafeDict(substitutions)))
    return formatted


def _run_service_hooks(
    hook_name: str,
    service_names: list[str],
    project_name: str,
    project_root: Path,
) -> None:
    if not service_names:
        return

    from phlo.plugins.discovery import ServiceDiscovery

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
                time.sleep(delay)

            command = _format_hook_command(hook.get("command"), substitutions)
            if not command:
                continue

            # Use project's venv python if command starts with 'python'
            if command and command[0] in ("python", "python3"):
                venv_python = project_root / ".venv" / "bin" / "python"
                if venv_python.exists():
                    command = [str(venv_python), *command[1:]]

            timeout = hook.get("timeout_seconds")
            if isinstance(timeout, str) and timeout.isdigit():
                timeout = int(timeout)
            elif not isinstance(timeout, int):
                timeout = None
            try:
                result = run_command(command, timeout_seconds=timeout, check=False)
            except Exception as exc:
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

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            state.pop(name, None)
            continue

        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            state.pop(name, None)
            continue
        except PermissionError:
            continue
        except Exception:
            continue

        for _ in range(4):
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

    from phlo.plugins.discovery import ServiceDiscovery

    discovery = ServiceDiscovery()
    service_names: list[str] = []

    for profile in profile_names:
        services = discovery.get_services_by_profile(profile)
        service_names.extend(s.name for s in services)

    return service_names


def _regenerate_compose(discovery, config: dict, phlo_dir: Path):
    """Regenerate docker-compose.yml based on current config."""
    from phlo.cli.infrastructure.selection import select_services_to_install
    from phlo.cli.infrastructure.utils import parse_env_file
    from phlo.plugins.compose import ComposeGenerator

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
    existing_env_local = parse_env_file(env_local_file)
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
