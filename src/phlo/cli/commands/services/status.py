"""Status command for showing service status."""

import click

from phlo.cli.commands.services.common import run_compose
from phlo.cli.commands.services.utils import ensure_phlo_dir, require_container_backend
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("status")
@click.option(
    "--backend",
    "backend_name",
    type=click.Choice(["docker", "podman", "auto"]),
    default=None,
    help="Container backend for this command.",
)
def status_cmd(backend_name: str | None):
    """Show status of Phlo infrastructure services.

    Examples:
        phlo services status
    """
    require_container_backend(backend_name)
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    logger.info(
        "services_status_requested",
        project_name=project_name,
        phlo_dir=str(phlo_dir),
    )

    cmd = compose_base_cmd(
        phlo_dir=phlo_dir,
        project_name=project_name,
        backend_name=backend_name,
    )
    cmd.extend(["ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"])

    result = run_compose(cmd, check=False, capture_output=False)
    if result.returncode != 0:
        logger.warning(
            "services_status_failed",
            project_name=project_name,
            returncode=result.returncode,
        )
        raise click.ClickException("No services running or error checking status.")
    logger.info("services_status_succeeded", project_name=project_name)
