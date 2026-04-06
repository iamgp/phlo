"""Stop command for stopping services."""

import sys
from pathlib import Path
from subprocess import TimeoutExpired
from uuid import uuid4

import click
import yaml

from phlo.cli.commands.services.utils import (
    _emit_service_lifecycle_events,
    _load_native_state,
    _stop_native_processes,
    ensure_phlo_dir,
    get_profile_service_names,
    require_docker,
)
from phlo.cli.infrastructure.command import run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("stop")
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
def stop_cmd(volumes: bool, stop_native: bool, profile: tuple[str, ...], service: tuple[str, ...]):
    """Stop Phlo infrastructure services.

    Examples:
        phlo services stop
        phlo services stop --volumes
        phlo services stop --profile observability
        phlo services stop --service postgres
        phlo services stop --service postgres,minio
    """
    project_root = Path.cwd()
    lifecycle_request_id = uuid4().hex
    logger.info(
        "services_stop_requested",
        project_name=get_project_name(),
        stop_native=stop_native,
        volumes=volumes,
        profile_count=len(profile),
        service_args_count=len(service),
    )
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
            logger.info(
                "services_stop_native_started",
                project_name=get_project_name(),
                service_count=len(native_targets),
                service_names=native_targets,
            )
            _emit_service_lifecycle_events(
                "pre_stop",
                native_targets,
                project_name=get_project_name(),
                project_root=project_root,
                request_id=lifecycle_request_id,
                metadata={"native": True},
            )
        _stop_native_processes(project_root, native_services_list or None)
        if native_targets:
            logger.info(
                "services_stop_native_completed",
                project_name=get_project_name(),
                service_count=len(native_targets),
                service_names=native_targets,
            )
            _emit_service_lifecycle_events(
                "post_stop",
                native_targets,
                project_name=get_project_name(),
                project_root=project_root,
                request_id=lifecycle_request_id,
                status="success",
                metadata={"native": True},
            )

    # If --native was explicitly requested, skip Docker unless --volumes or --profile also given.
    if stop_native and not volumes and not profile:
        logger.info("services_stop_native_only_completed", project_name=get_project_name())
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
    logger.info(
        "services_stop_targets_resolved",
        project_name=project_name,
        service_count=len(services_list),
        service_names=services_list,
    )

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
            request_id=lifecycle_request_id,
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
    logger.info(
        "services_stop_docker_started",
        project_name=project_name,
        service_count=len(services_list),
        service_names=services_list,
        volumes=volumes,
    )

    try:
        result = run_command(cmd, check=False, capture_output=False)
        if result.returncode == 0:
            logger.info(
                "services_stop_succeeded",
                project_name=project_name,
                service_count=len(docker_targets),
                service_names=docker_targets,
                volumes=volumes,
            )
            if docker_targets:
                _emit_service_lifecycle_events(
                    "post_stop",
                    docker_targets,
                    project_name=project_name,
                    project_root=project_root,
                    request_id=lifecycle_request_id,
                    status="success",
                    metadata={"native": False},
                )
            if services_list:
                click.echo(f"Stopped services: {', '.join(services_list)}")
            else:
                click.echo(f"{project_name} infrastructure stopped.")
        else:
            logger.error(
                "services_stop_failed",
                project_name=project_name,
                returncode=result.returncode,
                service_count=len(docker_targets),
                service_names=docker_targets,
                volumes=volumes,
            )
            if docker_targets:
                _emit_service_lifecycle_events(
                    "post_stop",
                    docker_targets,
                    project_name=project_name,
                    project_root=project_root,
                    request_id=lifecycle_request_id,
                    status="failure",
                    metadata={"native": False, "returncode": result.returncode},
                )
            click.echo(f"Error: docker compose failed with code {result.returncode}", err=True)
            click.echo(f"Command: {' '.join(cmd)}", err=True)
            sys.exit(result.returncode)
    except FileNotFoundError:
        logger.error("services_stop_docker_not_found", project_name=project_name, exc_info=True)
        click.echo("Error: docker command not found.", err=True)
        sys.exit(1)
    except TimeoutExpired:
        logger.error(
            "services_stop_timeout",
            project_name=project_name,
            command=" ".join(cmd),
            exc_info=True,
        )
        click.echo("Error: docker compose timed out.", err=True)
        click.echo(f"Command: {' '.join(cmd)}", err=True)
        sys.exit(1)
