"""CLI commands for the MinIO service."""

from __future__ import annotations

import subprocess
from shutil import which
from subprocess import TimeoutExpired

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir
from phlo.cli.infrastructure.command import CommandError, run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name


def _require_docker() -> None:
    """Validate that Docker is installed and responsive."""
    if which("docker") is None:
        raise click.ClickException("docker command not found.")
    try:
        result = run_command(
            ["docker", "info"],
            timeout_seconds=10,
            capture_output=True,
            check=False,
        )
    except TimeoutExpired as exc:
        raise click.ClickException("docker info timed out.") from exc
    if result.returncode != 0:
        raise click.ClickException("Docker is not running.")


def _mc_exec_base(*, tty: bool) -> list[str]:
    """Build the docker compose exec command for the MinIO container."""
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.append("exec")
    if not tty:
        cmd.append("-T")
    cmd.extend(["minio", "mc"])
    return cmd


@click.command(
    name="minio",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("mc_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def minio_group(ctx: click.Context, mc_args: tuple[str, ...]) -> None:
    """Run the MinIO client or MinIO helper commands inside the project service."""
    if mc_args and mc_args[0] == "ls":
        minio_ls.main(
            args=list(mc_args[1:]),
            prog_name="phlo minio ls",
            standalone_mode=False,
        )
        return
    if len(mc_args) >= 2 and mc_args[0] == "admin" and mc_args[1] == "info":
        minio_admin_info.main(
            args=list(mc_args[2:]),
            prog_name="phlo minio admin info",
            standalone_mode=False,
        )
        return

    _require_docker()
    cmd = _mc_exec_base(tty=True)
    cmd.extend(mc_args)
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise click.ClickException(f"mc exited with status {result.returncode}.")


@click.command(name="ls")
@click.argument("target", default="local/")
@click.option("--recursive", is_flag=True, help="List recursively.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON lines from mc.")
@click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
def minio_ls(target: str, recursive: bool, as_json: bool, timeout_seconds: int) -> None:
    """List objects or buckets using the MinIO client."""
    _require_docker()
    cmd = _mc_exec_base(tty=False)
    cmd.append("ls")
    if recursive:
        cmd.append("--recursive")
    if as_json:
        cmd.append("--json")
    cmd.append(target)

    try:
        result = run_command(
            cmd,
            timeout_seconds=timeout_seconds,
            capture_output=True,
            check=True,
        )
    except CommandError as exc:
        stderr = exc.stderr.strip()
        raise click.ClickException(stderr or str(exc)) from exc
    except TimeoutExpired as exc:
        raise click.ClickException(f"List timed out after {timeout_seconds} seconds.") from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)


@click.command(name="info")
@click.argument("target", default="local/")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output from mc.")
@click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
def minio_admin_info(target: str, as_json: bool, timeout_seconds: int) -> None:
    """Show MinIO admin info using the MinIO client."""
    _require_docker()
    cmd = _mc_exec_base(tty=False)
    cmd.extend(["admin", "info"])
    if as_json:
        cmd.append("--json")
    cmd.append(target)

    try:
        result = run_command(
            cmd,
            timeout_seconds=timeout_seconds,
            capture_output=True,
            check=True,
        )
    except CommandError as exc:
        stderr = exc.stderr.strip()
        raise click.ClickException(stderr or str(exc)) from exc
    except TimeoutExpired as exc:
        raise click.ClickException(
            f"Admin info timed out after {timeout_seconds} seconds."
        ) from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)
