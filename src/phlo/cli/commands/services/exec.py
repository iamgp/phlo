"""Exec command for running a process inside a service container."""

from __future__ import annotations

import subprocess

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir, require_docker
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


@click.command("exec", context_settings={"ignore_unknown_options": True})
@click.argument("service_name")
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@click.option("--tty/--no-tty", default=False, show_default=True, help="Allocate a TTY.")
def exec_cmd(service_name: str, command: tuple[str, ...], tty: bool) -> None:
    """Run a command inside a running Phlo service container.

    Examples:
        phlo services exec <service> -- dbt run --select my_model
        phlo services exec trino -- trino --execute "SELECT 1"
        phlo services exec --tty postgres -- psql
    """
    if not command:
        raise click.ClickException("Provide a command after `--`.")

    require_docker()
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    logger.info(
        "services_exec_requested",
        project_name=project_name,
        service_name=service_name,
        tty=tty,
        command=list(command),
    )

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.append("exec")
    if not tty:
        cmd.append("-T")
    cmd.append(service_name)
    cmd.extend(command)

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise click.ClickException(
            f"Command exited with status {result.returncode} in service {service_name}."
        )
