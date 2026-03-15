"""CLI commands for the PostgreSQL service."""

from __future__ import annotations

import gzip
import subprocess
from pathlib import Path
from shutil import which
from subprocess import TimeoutExpired

import click

from phlo.cli.commands.services.utils import ensure_phlo_dir
from phlo.cli.infrastructure.command import CommandError, run_command
from phlo.cli.infrastructure.compose import compose_base_cmd
from phlo.cli.infrastructure.utils import get_project_name
from phlo_postgres.settings import get_settings


def _read_sql(*, query: str | None, file: Path | None) -> str:
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


def _require_docker() -> None:
    """Validate that Docker CLI is installed."""
    if which("docker") is None:
        raise click.ClickException("docker command not found.")


def _postgres_exec_base(*, tty: bool) -> list[str]:
    """Build the docker compose exec command for the Postgres container."""
    phlo_dir = ensure_phlo_dir()
    project_name = get_project_name()
    cmd = compose_base_cmd(phlo_dir=phlo_dir, project_name=project_name)
    cmd.append("exec")
    if not tty:
        cmd.append("-T")
    cmd.append("postgres")
    return cmd


def _postgres_identity(*, user: str | None, database: str | None) -> tuple[str, str]:
    """Resolve effective Postgres user/database defaults."""
    settings = get_settings()
    return user or settings.postgres_user, database or settings.postgres_db


@click.command(
    name="postgres",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("postgres_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def postgres_group(ctx: click.Context, postgres_args: tuple[str, ...]) -> None:
    """Run psql or Postgres helper commands against the project database."""
    if postgres_args and postgres_args[0] == "query":
        postgres_query.main(
            args=list(postgres_args[1:]),
            prog_name="phlo postgres query",
            standalone_mode=False,
        )
        return
    if postgres_args and postgres_args[0] == "dump":
        postgres_dump.main(
            args=list(postgres_args[1:]),
            prog_name="phlo postgres dump",
            standalone_mode=False,
        )
        return
    if postgres_args and postgres_args[0] == "restore":
        postgres_restore.main(
            args=list(postgres_args[1:]),
            prog_name="phlo postgres restore",
            standalone_mode=False,
        )
        return
    if postgres_args and postgres_args[0] == "vacuum":
        postgres_vacuum.main(
            args=list(postgres_args[1:]),
            prog_name="phlo postgres vacuum",
            standalone_mode=False,
        )
        return

    _require_docker()
    user, database = _postgres_identity(user=None, database=None)
    cmd = _postgres_exec_base(tty=True)
    cmd.extend(["psql", "-U", user, "-d", database])
    cmd.extend(postgres_args)
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise click.ClickException(f"psql exited with status {result.returncode}.")


@click.command(name="query")
@click.argument("query", required=False)
@click.option(
    "--file",
    "query_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--user", default=None, help="Database user.")
@click.option("--db", "database", default=None, help="Database name.")
@click.option("--timeout", "timeout_seconds", default=30, show_default=True, type=int)
def postgres_query(
    query: str | None,
    query_file: Path | None,
    user: str | None,
    database: str | None,
    timeout_seconds: int,
) -> None:
    """Execute a SQL query against the running PostgreSQL service."""
    _require_docker()
    sql = _read_sql(query=query, file=query_file)
    resolved_user, resolved_db = _postgres_identity(user=user, database=database)
    cmd = _postgres_exec_base(tty=False)
    cmd.extend(["psql", "-U", resolved_user, "-d", resolved_db, "-v", "ON_ERROR_STOP=1", "-c", sql])

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


@click.command(name="dump")
@click.option(
    "--file",
    "output_file",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output path. Use .gz for gzip-compressed dumps.",
)
@click.option("--user", default=None, help="Database user.")
@click.option("--db", "database", default=None, help="Database name.")
@click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
def postgres_dump(
    output_file: Path,
    user: str | None,
    database: str | None,
    timeout_seconds: int,
) -> None:
    """Write a PostgreSQL logical backup to a local file."""
    _require_docker()
    resolved_user, resolved_db = _postgres_identity(user=user, database=database)
    cmd = _postgres_exec_base(tty=False)
    cmd.extend(["pg_dump", "-U", resolved_user, resolved_db])

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
        raise click.ClickException(f"Dump timed out after {timeout_seconds} seconds.") from exc

    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        if output_file.suffix == ".gz":
            with gzip.open(output_file, "wt", encoding="utf-8") as handle:
                handle.write(result.stdout)
        else:
            output_file.write_text(result.stdout, encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to write dump file: {output_file}") from exc

    click.echo(f"Wrote dump to {output_file}")


@click.command(name="restore")
@click.option(
    "--file",
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Input dump file. Supports .sql and .gz files.",
)
@click.option("--user", default=None, help="Database user.")
@click.option("--db", "database", default=None, help="Database name.")
@click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
def postgres_restore(
    input_file: Path,
    user: str | None,
    database: str | None,
    timeout_seconds: int,
) -> None:
    """Restore a PostgreSQL logical backup from a local file."""
    _require_docker()
    resolved_user, resolved_db = _postgres_identity(user=user, database=database)
    cmd = _postgres_exec_base(tty=False)
    cmd.extend(["psql", "-U", resolved_user, "-d", resolved_db, "-v", "ON_ERROR_STOP=1"])

    try:
        if input_file.suffix == ".gz":
            with gzip.open(input_file, "rt", encoding="utf-8") as handle:
                sql = handle.read()
        else:
            sql = input_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Failed to read restore file: {input_file}") from exc

    try:
        result = subprocess.run(
            cmd,
            input=sql,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except TimeoutExpired as exc:
        raise click.ClickException(f"Restore timed out after {timeout_seconds} seconds.") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise click.ClickException(stderr or f"Restore failed with status {result.returncode}.")

    click.echo(f"Restored {input_file} into {resolved_db}")


@click.command(name="vacuum")
@click.option("--user", default=None, help="Database user.")
@click.option("--db", "database", default=None, help="Database name.")
@click.option("--analyze/--no-analyze", default=True, show_default=True)
@click.option("--timeout", "timeout_seconds", default=120, show_default=True, type=int)
def postgres_vacuum(
    user: str | None,
    database: str | None,
    analyze: bool,
    timeout_seconds: int,
) -> None:
    """Run vacuumdb inside the PostgreSQL service container."""
    _require_docker()
    resolved_user, resolved_db = _postgres_identity(user=user, database=database)
    cmd = _postgres_exec_base(tty=False)
    cmd.extend(["vacuumdb", "-U", resolved_user])
    if analyze:
        cmd.append("-z")
    cmd.append(resolved_db)

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
        raise click.ClickException(f"Vacuum timed out after {timeout_seconds} seconds.") from exc

    if result.stdout:
        click.echo(result.stdout, nl=False)
