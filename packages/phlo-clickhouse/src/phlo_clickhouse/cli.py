"""CLI commands for the ClickHouse data plane service."""

from __future__ import annotations

from pathlib import Path
from shutil import which
from subprocess import TimeoutExpired

import click

from phlo.cli.infrastructure.command import CommandError, run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo.logging import get_logger

logger = get_logger(__name__)


def _read_query(*, query: str | None, file: Path | None) -> str:
    """Return SQL text from inline query or file input."""
    if query and file:
        raise click.ClickException("Use either an inline query or --file, not both.")
    if file is not None:
        try:
            sql = file.read_text(encoding="utf-8")
        except OSError as exc:
            raise click.ClickException(f"Failed to read SQL file: {file}") from exc
        if sql.strip():
            return sql
        raise click.ClickException(f"SQL file is empty: {file}")
    if query and query.strip():
        return query
    raise click.ClickException("Provide a SQL query argument or --file.")


def _ensure_phlo_dir() -> Path:
    """Return the local .phlo directory or exit with a clear error."""
    phlo_dir = Path.cwd() / ".phlo"
    if phlo_dir.exists():
        return phlo_dir
    raise click.ClickException(".phlo directory not found. Run 'phlo services init' first.")


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
    if result.returncode == 0:
        return
    raise click.ClickException("Docker is not running.")


@click.group(name="clickhouse")
def clickhouse_group() -> None:
    """Query and inspect the ClickHouse data plane service."""


@clickhouse_group.command(name="query")
@click.argument("query", required=False)
@click.option(
    "--file",
    "query_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--format", "output_format", default="TabSeparatedRaw", show_default=True)
@click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
def clickhouse_query(
    query: str | None,
    query_file: Path | None,
    output_format: str,
    timeout_seconds: int,
) -> None:
    """Execute a SQL query against the running ClickHouse service."""
    _require_docker()
    phlo_dir = _ensure_phlo_dir()
    project_name = get_project_name()
    sql = _read_query(query=query, file=query_file)

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(
        [
            "exec",
            "-T",
            "clickhouse",
            "clickhouse-client",
            "--multiquery",
            "--format",
            output_format,
            "--query",
            sql,
        ]
    )

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
        raise click.ClickException(f"Query timed out after {timeout_seconds} seconds.") from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)


@clickhouse_group.command(name="status")
def clickhouse_status() -> None:
    """Show ClickHouse service status and basic server info."""
    _require_docker()
    phlo_dir = _ensure_phlo_dir()
    project_name = get_project_name()

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(
        [
            "exec",
            "-T",
            "clickhouse",
            "clickhouse-client",
            "--query",
            "SELECT version() AS version, uptime() AS uptime_seconds, "
            "currentDatabase() AS current_database",
        ]
    )

    try:
        result = run_command(
            cmd,
            timeout_seconds=10,
            capture_output=True,
            check=True,
        )
    except CommandError as exc:
        stderr = exc.stderr.strip()
        raise click.ClickException(stderr or str(exc)) from exc
    except TimeoutExpired as exc:
        raise click.ClickException("Status check timed out.") from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)
