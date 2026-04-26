"""Restart command for restarting services."""

import click

from phlo.cli.commands.services.common import (
    parse_service_args,
    run_compose,
    validate_requested_profiles,
)
from phlo.cli.commands.services.utils import (
    ensure_phlo_dir,
    get_profile_service_names,
    require_container_backend,
)
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("restart")
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
@click.option(
    "--backend",
    "backend_name",
    type=click.Choice(["docker", "podman", "auto"]),
    default=None,
    help="Container backend for this command.",
)
def restart_cmd(
    build: bool,
    profile: tuple[str, ...],
    service: tuple[str, ...],
    dev: bool,
    backend_name: str | None,
):
    """Restart Phlo infrastructure services (stop + start).

    Combines stop and start in a single command for convenience.

    Examples:
        phlo services restart                          # Restart all services
        phlo services restart --profile observability  # Restart profile services only
        phlo services restart --service postgres       # Restart specific service
        phlo services restart --build                  # Rebuild before starting
    """
    require_container_backend(backend_name)
    if dev:
        logger.warning("services_restart_dev_mode_not_supported")
        raise click.UsageError("dev mode not implemented for restart")

    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    profile = validate_requested_profiles(profile)
    logger.info(
        "services_restart_requested",
        project_name=project_name,
        build=build,
        profile_count=len(profile),
    )

    # Parse comma-separated services
    services_list = parse_service_args(service)

    # When --profile is specified without --service, target only profile services
    if profile and not services_list:
        services_list = get_profile_service_names(profile)
        if not services_list:
            profile_list = ", ".join(profile)
            logger.warning(
                "services_restart_profile_resolved_empty",
                project_name=project_name,
                profiles=profile_list,
            )
            raise click.UsageError(f"profile(s) resolve to no services: {profile_list}")
    logger.info(
        "services_restart_targets_resolved",
        project_name=project_name,
        service_count=len(services_list),
        service_names=services_list,
    )

    if services_list:
        click.echo(f"Restarting services: {', '.join(services_list)}...")
    else:
        click.echo(f"Restarting {project_name} infrastructure...")

    # Stop services
    cmd = compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name=project_name,
        profiles=profile,
        backend_name=backend_name,
    )
    if services_list:
        cmd.extend(["stop", *services_list])
    else:
        cmd.append("down")
    logger.info(
        "services_restart_stop_started",
        project_name=project_name,
        service_count=len(services_list),
        service_names=services_list,
    )

    result = run_compose(cmd, check=False, capture_output=False)
    if result.returncode != 0:
        logger.warning(
            "services_restart_stop_failed",
            project_name=project_name,
            returncode=result.returncode,
            service_count=len(services_list),
            service_names=services_list,
        )
        click.echo(f"Warning: stop failed with code {result.returncode}", err=True)
    else:
        logger.info(
            "services_restart_stop_completed",
            project_name=project_name,
            service_count=len(services_list),
            service_names=services_list,
        )

    # Start services
    click.echo("")
    cmd = compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name=project_name,
        profiles=profile,
        backend_name=backend_name,
    )
    cmd.extend(["up", "-d"])

    if build:
        cmd.append("--build")

    if services_list:
        cmd.extend(services_list)
    logger.info(
        "services_restart_start_started",
        project_name=project_name,
        service_count=len(services_list),
        service_names=services_list,
        build=build,
    )

    result = run_compose(cmd, check=False, capture_output=False)
    if result.returncode == 0:
        logger.info(
            "services_restart_succeeded",
            project_name=project_name,
            service_count=len(services_list),
            service_names=services_list,
            build=build,
        )
        click.echo("")
        if services_list:
            click.echo(f"Restarted services: {', '.join(services_list)}")
        else:
            click.echo(f"{project_name} infrastructure restarted.")
    else:
        logger.error(
            "services_restart_start_failed",
            project_name=project_name,
            returncode=result.returncode,
            service_count=len(services_list),
            service_names=services_list,
        )
        raise click.ClickException(
            f"container compose failed with code {result.returncode}: {' '.join(cmd)}"
        )
