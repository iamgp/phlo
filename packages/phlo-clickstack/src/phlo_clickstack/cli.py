"""CLI commands for querying ClickStack's bundled ClickHouse service.

This module provides Click CLI commands for executing SQL queries against
the running ClickStack ClickHouse container. It includes utilities for
validating Docker availability, reading SQL from files or inline arguments,
and executing queries with configurable formatting.
"""

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
    """Read and validate SQL query from inline argument or file.

    Accepts either an inline SQL query string or a path to a SQL file.
    Validates that exactly one input source is provided and that the
    content is non-empty.

    Args:
        query: Inline SQL query string, or None if reading from file.
        file: Path to SQL file, or None if using inline query.

    Returns:
        str: The SQL query text to execute.

    Raises:
        click.ClickException: If both query and file are provided.
        click.ClickException: If file cannot be read.
        click.ClickException: If file is empty or contains only whitespace.
        click.ClickException: If neither query nor file is provided.

    """
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
    """Locate and return the local .phlo directory.

    Searches for a .phlo directory in the current working directory.
    This directory is required for Docker Compose project configuration.

    Returns:
        Path: Path to the .phlo directory.

    Raises:
        click.ClickException: If .phlo directory does not exist.

    """
    phlo_dir = Path.cwd() / ".phlo"
    if phlo_dir.exists():
        return phlo_dir
    raise click.ClickException(".phlo directory not found. Run 'phlo services init' first.")


def _require_docker() -> None:
    """Validate Docker installation and daemon status.

    Checks that the Docker CLI is available in PATH and that the
    Docker daemon is responsive. Times out after 10 seconds.

    Raises:
        click.ClickException: If docker command is not found.
        click.ClickException: If docker info times out.
        click.ClickException: If Docker daemon is not running.

    """
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


@click.group(name="clickstack")
def clickstack_group() -> None:
    """Query and inspect the ClickStack service.

    Provides commands for interacting with the ClickStack ClickHouse
    container, including executing SQL queries.
    """


@clickstack_group.command(name="query")
@click.argument("query", required=False)
@click.option("--file", "query_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--format", "output_format", default="TabSeparatedRaw", show_default=True)
@click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
def clickstack_query(
    query: str | None,
    query_file: Path | None,
    output_format: str,
    timeout_seconds: int,
) -> None:
    """Execute a ClickHouse query against the running ClickStack service.

    Runs a SQL query via clickhouse-client inside the ClickStack container.
    Accepts SQL either as a command argument or from a file. Requires Docker
    and a running phlo services stack with ClickStack enabled.

    Args:
        query: SQL query string to execute.
        query_file: Path to file containing SQL query.
        output_format: ClickHouse output format (default: TabSeparatedRaw).
        timeout_seconds: Query execution timeout in seconds.

    Raises:
        click.ClickException: If Docker is unavailable.
        click.ClickException: If .phlo directory is missing.
        click.ClickException: If both query and file options provided.
        click.ClickException: If query file cannot be read.
        click.ClickException: If query execution fails.
        click.ClickException: If query times out.

    """
    _require_docker()
    phlo_dir = _ensure_phlo_dir()
    project_name = get_project_name()
    sql = _read_query(query=query, file=query_file)

    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.extend(
        [
            "exec",
            "-T",
            "clickstack",
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
