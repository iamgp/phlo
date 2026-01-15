"""Start command for starting services."""

import asyncio
import signal
import subprocess
import sys
import time
from pathlib import Path

import click
import yaml

from phlo.cli.commands.services.utils import (
    _emit_service_lifecycle_events,
    _load_native_state,
    _run_service_hooks,
    _save_native_state,
    _stop_native_processes,
    ensure_phlo_dir,
    get_profile_service_names,
    require_docker,
)
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.discovery import ServiceDefinition


@click.command("start")
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
def start_cmd(
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
        from phlo.plugins.compose.native import NativeProcessManager

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
                from phlo.discovery import ServiceDiscovery
                from phlo.plugins.compose.native import NativeProcessManager

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
    except Exception:
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
