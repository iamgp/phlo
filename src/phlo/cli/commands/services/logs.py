"""Logs command for viewing service logs."""

import click

from phlo.cli.commands.services.common import run_compose
from phlo.cli.commands.services.utils import ensure_phlo_dir, require_container_backend
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("logs")
@click.argument("service", required=False)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
@click.option("-n", "--tail", default=100, help="Number of lines to show")
@click.option(
    "--backend",
    "backend_name",
    type=click.Choice(["docker", "podman", "auto"]),
    default=None,
    help="Container backend for this command.",
)
def logs_cmd(service: str | None, follow: bool, tail: int, backend_name: str | None):
    """View logs from Phlo infrastructure services.

    Examples:
        phlo services logs
        phlo services logs dagster
        phlo services logs -f
    """
    require_container_backend(backend_name)
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    logger.info(
        "services_logs_requested",
        project_name=project_name,
        service_name=service,
        follow=follow,
        tail=tail,
    )

    cmd = compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name=project_name,
        backend_name=backend_name,
    )
    cmd.extend(["logs", "--tail", str(tail)])

    if follow:
        cmd.append("-f")

    if service:
        cmd.append(service)

    try:
        result = run_compose(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            logger.warning(
                "services_logs_failed",
                project_name=project_name,
                service_name=service,
                returncode=result.returncode,
            )
            exc = click.ClickException(
                f"container compose failed with code {result.returncode}: {' '.join(cmd)}"
            )
            exc.exit_code = result.returncode
            raise exc
        logger.info(
            "services_logs_completed",
            project_name=project_name,
            service_name=service,
        )
    except KeyboardInterrupt:
        logger.warning(
            "services_logs_interrupted",
            project_name=project_name,
            service_name=service,
        )
