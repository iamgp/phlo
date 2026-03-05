"""CLI plugin for dbt-related commands."""

from __future__ import annotations

import subprocess
import sys

import click

from phlo.logging import get_logger
from phlo.plugins.base import CliCommandPlugin, PluginMetadata
from phlo_dbt.cli_publishing import publishing
from phlo_dbt.runtime_config import ensure_dbt_profile


def _run_dbt(subcommand: str, target: str, select_expr: str | None = None) -> None:
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


@click.group("dbt")
def dbt_group() -> None:
    """dbt commands (compile, run, test, publishing)."""


@dbt_group.command("compile")
@click.option("--target", default="dev", help="dbt target profile")
def compile_cmd(target: str) -> None:
    """Compile dbt models in the local project."""
    _run_dbt("compile", target)


@dbt_group.command("run")
@click.option("--target", default="dev", help="dbt target profile")
@click.option("--select", "select_expr", default=None, help="dbt model selector")
def run_cmd(target: str, select_expr: str | None) -> None:
    """Run dbt models in the local project."""
    _run_dbt("run", target, select_expr)


@dbt_group.command("test")
@click.option("--target", default="dev", help="dbt target profile")
@click.option("--select", "select_expr", default=None, help="dbt model selector")
def test_cmd(target: str, select_expr: str | None) -> None:
    """Run dbt tests in the local project."""
    _run_dbt("test", target, select_expr)


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
