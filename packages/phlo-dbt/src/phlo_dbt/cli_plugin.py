"""CLI plugin for dbt-related commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger
from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dbt.cli_publishing import publishing
from phlo_dbt.runtime_config import DEFAULT_DBT_TARGET, ensure_dbt_profile


def _container_path(path: Path, *, project_root: Path) -> str:
    """Translate a project-local host path into the orchestrator container mount path."""
    relative = path.resolve().relative_to(project_root.resolve())
    return str(Path("/app") / relative)


def _should_run_in_container(local: bool) -> bool:
    """Choose the default execution environment for dbt commands."""
    if local:
        return False
    try:
        ensure_phlo_dir()
    except SystemExit:
        return False
    return True


def _resolve_exec_service_name() -> str:
    """Resolve the execution service from the active orchestrator adapter."""
    from phlo.orchestrators import get_active_orchestrator

    adapter = get_active_orchestrator()
    service_name = adapter.exec_service_name()
    if not service_name:
        raise click.ClickException(
            "The active orchestrator does not expose a container execution service. "
            "Use --local to run dbt on the host."
        )
    return service_name


def _run_dbt_in_container(
    *,
    subcommand: str,
    target: str,
    select_expr: str | None = None,
) -> None:
    """Run dbt inside the active orchestrator service container."""
    from phlo_dbt.settings import get_settings

    logger = get_logger(f"phlo.dbt.{subcommand}")
    settings = get_settings()
    project_root = Path.cwd()
    project_dir = settings.dbt_project_path
    profiles_dir = settings.dbt_profiles_path
    exec_service_name = _resolve_exec_service_name()

    if not (project_dir / "dbt_project.yml").exists():
        click.echo(f"No dbt project found at {project_dir}", err=True)
        sys.exit(1)

    phlo_dir = ensure_phlo_dir()
    compose_cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=get_project_name())
    cmd = [*compose_cmd, "exec", "-T", exec_service_name, "dbt", subcommand]
    cmd.extend(["--project-dir", _container_path(project_dir, project_root=project_root)])
    cmd.extend(["--profiles-dir", _container_path(profiles_dir, project_root=project_root)])
    cmd.extend(["--target", target])
    if select_expr is not None:
        cmd.extend(["--select", select_expr])

    click.echo(f"Running dbt {subcommand} in {exec_service_name}...")
    logger.debug(
        f"dbt_{subcommand}_container_started",
        project_dir=str(project_dir),
        service_name=exec_service_name,
        target=target,
        select=select_expr,
    )
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: docker command not found", err=True)
        sys.exit(1)


def _run_dbt_local(subcommand: str, target: str, select_expr: str | None = None) -> None:
    """Run a dbt subcommand against the local project.

    Args:
        subcommand: dbt subcommand to execute (compile, run, test).
        target: dbt target profile name.
        select_expr: Optional dbt model selector expression.
    """
    from phlo_dbt.settings import get_settings

    logger = get_logger(f"phlo.dbt.{subcommand}")
    settings = get_settings()
    project_dir = settings.dbt_project_path
    profiles_dir = settings.dbt_profiles_path

    if not (project_dir / "dbt_project.yml").exists():
        click.echo(f"No dbt project found at {project_dir}", err=True)
        sys.exit(1)

    ensure_dbt_profile(profiles_dir, target=target)

    cmd = [
        "dbt",
        subcommand,
        "--profiles-dir",
        str(profiles_dir),
        "--target",
        target,
    ]
    if select_expr is not None:
        cmd.extend(["--select", select_expr])

    click.echo(f"Running dbt {subcommand} at {project_dir}...")
    logger.debug(
        f"dbt_{subcommand}_started",
        project_dir=str(project_dir),
        target=target,
        select=select_expr,
    )
    try:
        result = subprocess.run(cmd, cwd=str(project_dir), check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: dbt command not found", err=True)
        sys.exit(1)


def _run_dbt(
    subcommand: str,
    target: str,
    select_expr: str | None = None,
    *,
    local: bool,
) -> None:
    """Run a dbt subcommand locally or inside the orchestrator container."""
    if _should_run_in_container(local):
        _run_dbt_in_container(subcommand=subcommand, target=target, select_expr=select_expr)
        return
    _run_dbt_local(subcommand, target, select_expr)


@click.group("dbt")
def dbt_group() -> None:
    """dbt commands (compile, run, test, publishing)."""


@dbt_group.command("compile")
@click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
@click.option(
    "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
)
def compile_cmd(target: str, local: bool) -> None:
    """Compile dbt models in the local project."""
    _run_dbt("compile", target, local=local)


@dbt_group.command("run")
@click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
@click.option("--select", "select_exprs", multiple=True, help="dbt model selector")
@click.option(
    "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
)
def run_cmd(target: str, select_exprs: tuple[str, ...], local: bool) -> None:
    """Run dbt models in the local project."""
    _run_dbt("run", target, " ".join(select_exprs) or None, local=local)


@dbt_group.command("test")
@click.option("--target", default=DEFAULT_DBT_TARGET, help="dbt target profile")
@click.option("--select", "select_exprs", multiple=True, help="dbt model selector")
@click.option(
    "--local", is_flag=True, help="Run dbt on the host instead of in the orchestrator container."
)
def test_cmd(target: str, select_exprs: tuple[str, ...], local: bool) -> None:
    """Run dbt tests in the local project."""
    _run_dbt("test", target, " ".join(select_exprs) or None, local=local)


dbt_group.add_command(publishing)


class DbtCliPlugin(CliCommandPlugin):
    """CLI plugin exposing dbt-related commands."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            Metadata describing the dbt CLI plugin.
        """
        return PluginMetadata(
            name="dbt",
            version="0.1.0",
            description="dbt CLI commands",
        )

    def get_cli_commands(self) -> list[click.Command]:
        """Return CLI commands contributed by this plugin.

        Returns:
            List of click commands to register.
        """
        return [dbt_group]
