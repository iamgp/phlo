"""CLI commands for Sling replication management."""

from __future__ import annotations

import os
import subprocess

import click

from phlo.logging import get_logger

logger = get_logger(__name__)


@click.group("sling")
def sling_group() -> None:
    """Sling replication commands."""


@sling_group.command("run")
@click.option("--replication", "-r", type=click.Path(exists=True), help="Sling replication YAML.")
@click.option("--source", "-s", help="Source connection name.")
@click.option("--target", "-t", help="Target connection name.")
@click.option("--stream", help="Source stream (e.g., 'public.users').")
@click.option("--mode", default="incremental", help="Replication mode.")
def run_command(
    replication: str | None,
    source: str | None,
    target: str | None,
    stream: str | None,
    mode: str,
) -> None:
    """Run a Sling replication.

    Either provide --replication YAML or --source/--stream/--target for ad-hoc runs.
    """
    from sling import Replication, Sling

    from phlo_sling.connections import export_sling_env, resolve_phlo_connections

    connections = resolve_phlo_connections()
    for key, value in export_sling_env(connections).items():
        os.environ.setdefault(key, value)

    if replication:
        click.echo(f"Running replication from {replication}")
        repl = Replication(file_path=replication)
        repl.run()
    elif source and stream:
        click.echo(f"Replicating {stream} from {source}")
        config = Sling(
            src_conn=source,
            src_stream=stream,
            tgt_conn=target,
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
        subprocess.run(["sling", "conns"], check=True)
    except Exception as exc:
        click.echo(f"  Could not list native connections: {exc}")


@sling_group.command("discover")
@click.argument("connection")
@click.option("--schema", help="Filter by schema name.")
@click.option("--format", "output_format", default="table", help="Output format (table, json).")
def discover_command(connection: str, schema: str | None, output_format: str) -> None:
    """Discover available streams from a Sling connection.

    Lists tables/views available in the source connection for use as
    stream_name in @phlo_sling_replication decorators.
    """
    from sling import Sling

    from phlo_sling.connections import export_sling_env, resolve_phlo_connections

    connections = resolve_phlo_connections()
    for key, value in export_sling_env(connections).items():
        os.environ.setdefault(key, value)

    click.echo(f"Discovering streams from {connection}...")
    try:
        config = Sling(src_conn=connection)
        config.run()
    except Exception as exc:
        raise click.ClickException(f"Discovery failed: {exc}") from exc
