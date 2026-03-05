"""Shared utilities for services commands."""

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import cast

import click

from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.utils import _resolve_container_name
from phlo.logging import get_logger
from phlo.utils import dedupe_preserve_order

logger = get_logger(__name__)

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
        logger.debug("docker_check_failed")
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
    if env_path and (resolved := resolve_phlo_package_dir(Path(env_path))):
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
    """Extract service environment overrides from configuration.

    Args:
        config: Loaded project configuration dictionary.

    Returns:
        Environment override mapping, or an empty mapping.
    """
    env_overrides = config.get("env", {})
    return env_overrides if isinstance(env_overrides, dict) else {}


def get_enabled_disabled_service_names(config: dict | None) -> tuple[set[str], set[str]]:
    """Return enabled/disabled service names from top-level service config.

    Supports both state formats:
    - list form: ``services.enabled`` / ``services.disabled``
    - mapping form: ``services.<name>.enabled: true|false``
    """
    if not isinstance(config, dict):
        return set(), set()

    services_config = config.get("services", {})
    if not isinstance(services_config, dict):
        return set(), set()

    def _clean_name(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    enabled_names: set[str] = set()
    disabled_names: set[str] = set()

    enabled_list = services_config.get("enabled")
    if isinstance(enabled_list, list):
        for name in enabled_list:
            if normalized := _clean_name(name):
                enabled_names.add(normalized)

    disabled_list = services_config.get("disabled")
    if isinstance(disabled_list, list):
        for name in disabled_list:
            if normalized := _clean_name(name):
                disabled_names.add(normalized)

    for name, service_config in services_config.items():
        if not isinstance(service_config, dict):
            continue
        normalized_name = _clean_name(name)
        if not normalized_name:
            continue
        if service_config.get("enabled") is False:
            disabled_names.add(normalized_name)
        elif service_config.get("enabled") is True:
            enabled_names.add(normalized_name)

    disabled_names.difference_update(enabled_names)
    return enabled_names, disabled_names


def _normalize_service_name_list(names: object) -> list[str]:
    """Normalize a service name list to unique lowercase names."""
    if not isinstance(names, list):
        return []

    normalized = [name.strip().lower() for name in names if isinstance(name, str) and name.strip()]
    return dedupe_preserve_order(normalized)


def normalize_services_enabled_disabled_config(
    config: dict[str, object],
) -> tuple[list[str], list[str]]:
    """Normalize services enabled/disabled lists and resolve contradictions.

    Rules:
        - Missing/non-list values become empty lists.
        - Service names are stripped, lowercased, deduplicated.
        - Deterministic ordering via sort.
        - If a name appears in both lists, disabled takes precedence.
    """
    services_config_value = config.get("services")
    if isinstance(services_config_value, dict):
        services_config = cast(dict[str, object], services_config_value)
    else:
        services_config = {}
        config["services"] = services_config

    enabled_names = _normalize_service_name_list(services_config.get("enabled"))
    disabled_names = _normalize_service_name_list(services_config.get("disabled"))
    conflicted_names = set(enabled_names).intersection(disabled_names)
    if conflicted_names:
        enabled_names = [name for name in enabled_names if name not in conflicted_names]

    enabled_names = sorted(enabled_names)
    disabled_names = sorted(disabled_names)
    services_config["enabled"] = enabled_names
    services_config["disabled"] = disabled_names
    return enabled_names, disabled_names


def _warn_secret_env_overrides(env_overrides: dict[str, object], services: list) -> None:
    """Warn when config env overrides include secret-backed service variables.

    Args:
        env_overrides: User-defined environment override mapping.
        services: Service definitions that declare environment variables.
    """
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
    """Normalize hook configuration to a list of mapping entries.

    Args:
        hooks: Raw hook configuration value.

    Returns:
        Normalized list of hook entry dictionaries.
    """
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
    """Format hook command tokens with safe placeholder substitution.

    Args:
        command: Hook command value from service config.
        substitutions: Placeholder values for command formatting.

    Returns:
        Formatted command tokens.
    """
    if isinstance(command, str):
        command = [command]
    if not isinstance(command, list):
        return []

    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            """Return an empty string for unknown placeholders."""
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
    """Execute configured service hooks for a lifecycle event.

    Args:
        hook_name: Lifecycle hook name to execute.
        service_names: Target service names.
        project_name: Active project name.
        project_root: Project root path.
    """
    if not service_names:
        return

    from phlo.plugins.discovery import ServiceDiscovery

    logger.debug(
        "service_hook_execution_started",
        hook_name=hook_name,
        service_count=len(service_names),
    )
    discovery = ServiceDiscovery()
    executed_count = 0
    failed_count = 0
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
                    logger.debug(
                        "service_hook_skipped_missing_dependency",
                        hook_name=hook_name,
                        service_name=service.name,
                        required_module=required_module,
                    )
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
                else:
                    command = [sys.executable, *command[1:]]

            timeout = hook.get("timeout_seconds")
            if isinstance(timeout, str) and timeout.isdigit():
                timeout = int(timeout)
            elif not isinstance(timeout, int):
                timeout = None
            command_name = command[0] if command else ""
            command_started = time.perf_counter()
            logger.debug(
                "service_hook_command_started",
                hook_name=hook_name,
                service_name=service.name,
                command_name=command_name,
                arg_count=max(len(command) - 1, 0),
                timeout_seconds=timeout,
            )
            try:
                result = run_command(command, timeout_seconds=timeout, check=False)
            except Exception as exc:
                failed_count += 1
                click.echo(
                    f"Warning: hook '{hook_name}' for {service.name} failed: {exc}",
                    err=True,
                )
                logger.warning(
                    "service_hook_command_failed",
                    hook_name=hook_name,
                    service_name=service.name,
                    command_name=command_name,
                    error=str(exc),
                    elapsed_ms=round((time.perf_counter() - command_started) * 1000, 2),
                )
                continue
            executed_count += 1
            logger.debug(
                "service_hook_command_completed",
                hook_name=hook_name,
                service_name=service.name,
                command_name=command_name,
                returncode=result.returncode,
                elapsed_ms=round((time.perf_counter() - command_started) * 1000, 2),
            )
            if result.returncode != 0:
                failed_count += 1
                click.echo(
                    f"Warning: hook '{hook_name}' for {service.name} failed: {result.stderr}",
                    err=True,
                )
                logger.warning(
                    "service_hook_command_nonzero_exit",
                    hook_name=hook_name,
                    service_name=service.name,
                    command_name=command_name,
                    returncode=result.returncode,
                )
    logger.debug(
        "service_hook_execution_completed",
        hook_name=hook_name,
        executed_count=executed_count,
        failed_count=failed_count,
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
    """Emit lifecycle hook events for each service in scope.

    Args:
        phase: Lifecycle phase name.
        service_names: Target service names.
        project_name: Active project name.
        project_root: Project root path.
        status: Optional lifecycle status value.
        metadata: Optional extra metadata attached to emitted events.
    """
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
    """Return the filesystem path for persisted native service state."""
    return project_root / ".phlo" / NATIVE_STATE_FILE


def _load_native_state(project_root: Path) -> dict[str, dict]:
    """Load persisted native process state for a project.

    Args:
        project_root: Project root path.

    Returns:
        Mapping of service names to persisted process metadata.
    """
    path = _native_state_path(project_root)
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            return json.load(f) or {}
    except (json.JSONDecodeError, OSError) as e:
        click.echo(f"Warning: Failed to read native state file {path}: {e}", err=True)
        return {}


def _save_native_state(project_root: Path, state: dict[str, dict]) -> None:
    """Atomically save native process state for a project.

    Args:
        project_root: Project root path.
        state: Native process state to persist.
    """
    path = _native_state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(path)


def _stop_native_processes(project_root: Path, service_names: list[str] | None = None) -> None:
    """Stop tracked native service processes and update persisted state.

    Args:
        project_root: Project root path.
        service_names: Optional subset of service names to stop.
    """
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
            logger.warning("process_kill_failed", name=name, pid=pid)
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

    # Get enabled/disabled services from normalized config
    enabled_names, disabled_names = normalize_services_enabled_disabled_config(config)

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
