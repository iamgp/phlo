"""CLI commands for Sling replication management."""

from __future__ import annotations

import json
import subprocess

import click

from phlo.logging import get_logger
from phlo_sling.connections import apply_sling_connection_env
from phlo_sling.settings import get_settings

logger = get_logger(__name__)


@click.group("sling")
def sling_group() -> None:
    """Sling replication commands."""


@sling_group.command("run")
@click.option("--replication", "-r", type=click.Path(exists=True), help="Sling replication YAML.")
@click.option("--source", "-s", help="Source connection name.")
@click.option("--target", "-t", help="Target connection name.")
@click.option("--stream", help="Source stream (e.g., 'public.users').")
@click.option("--object", "target_object", help="Target object/table name.")
@click.option("--mode", default="incremental", help="Replication mode.")
def run_command(
    replication: str | None,
    source: str | None,
    target: str | None,
    stream: str | None,
    target_object: str | None,
    mode: str,
) -> None:
    """Run a Sling replication.

    Either provide --replication YAML or --source/--stream/--target for ad-hoc runs.
    """
    from sling import Replication, Sling

    apply_sling_connection_env()

    if replication:
        click.echo(f"Running replication from {replication}")
        repl = Replication(file_path=replication)
        repl.run()
    elif source and stream:
        if not target:
            raise click.UsageError("Provide --target for ad-hoc runs.")
        resolved_target_object = _resolve_target_object(stream=stream, target_object=target_object)
        click.echo(f"Replicating {stream} from {source}")
        config = Sling(
            src_conn=source,
            src_stream=stream,
            tgt_conn=target,
            tgt_object=resolved_target_object,
            mode=mode,
        )
        config.run()
    else:
        raise click.UsageError("Provide --replication YAML or --source/--stream.")


@sling_group.command("conns")
@click.option("--auto/--no-auto", default=True, help="Include auto-discovered connections.")
def conns_command(auto: bool) -> None:
    """List available Sling connections.

    Shows auto-discovered connections from Phlo capability metadata and any
    connections from explicit env.yaml files.
    """
    if auto:
        from phlo_sling.connections import resolve_phlo_connections

        connections = resolve_phlo_connections()
        if connections:
            click.echo("Auto-discovered connections:")
            for name, config in connections.items():
                conn_type = config.get("type", "unknown")
                host = config.get("host") or config.get("endpoint", "")
                click.echo(f"  {name}: {conn_type} ({host})")
        else:
            click.echo("No auto-discovered connections found.")

    click.echo("\nSling native connections:")
    try:
        result = _run_sling_cli_command(["conns", "list"])
        click.echo(result.stdout, nl=False)
    except Exception as exc:
        click.echo(f"  Could not list native connections: {exc}")


@sling_group.command("discover")
@click.argument("connection")
@click.option("--schema", help="Filter by schema name.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format.",
)
def discover_command(connection: str, schema: str | None, output_format: str) -> None:
    """Discover available streams from a Sling connection.

    Lists tables/views available in the source connection for use as
    stream_name in @phlo_sling_replication decorators.
    """
    apply_sling_connection_env()

    click.echo(f"Discovering streams from {connection}...")
    try:
        command = ["conns", "discover", connection]
        if schema:
            command.extend(["--pattern", f"{schema}.*"])

        result = _run_sling_cli_command(command)
        if output_format == "json":
            click.echo(json.dumps(_parse_discovery_output(result.stdout), indent=2))
            return

        click.echo(result.stdout, nl=False)
    except Exception as exc:
        raise click.ClickException(f"Discovery failed: {exc}") from exc


def _resolve_target_object(stream: str, target_object: str | None) -> str:
    """Resolve the destination object for an ad-hoc Sling run."""
    if target_object:
        return target_object
    if "*" in stream:
        raise click.UsageError("Provide --object when --stream uses a wildcard.")
    return stream


def _get_sling_binary() -> str:
    """Return the Sling binary path, honoring package settings."""
    settings = get_settings()
    if settings.sling_binary_path:
        return settings.sling_binary_path

    from sling.bin import SLING_BIN

    return SLING_BIN


def _run_sling_cli_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute the Sling CLI and return captured output."""
    return subprocess.run(
        [_get_sling_binary(), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _parse_discovery_output(output: str) -> list[dict[str, str]]:
    """Parse Sling's ASCII discovery table into JSON-serializable rows."""
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    table_lines = [line for line in lines if "|" in line]
    if len(table_lines) < 2:
        raise ValueError("Unexpected Sling discovery output format.")

    headers = [_normalize_column_name(part) for part in table_lines[0].split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[1:]:
        values = [part.strip() for part in line.split("|")]
        if len(values) != len(headers):
            continue
        if all(set(value) <= {"-"} for value in values):
            continue
        rows.append(dict(zip(headers, values, strict=True)))

    if not rows:
        raise ValueError("No streams found in Sling discovery output.")

    return rows


def _normalize_column_name(value: str) -> str:
    """Normalize discovery table headers for JSON output."""
    return value.strip().lower().replace(" ", "_")
