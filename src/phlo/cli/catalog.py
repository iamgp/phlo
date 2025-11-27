"""
Iceberg catalog management CLI commands.

Provides commands to:
- List and describe Iceberg tables
- View table snapshots and history
- Manage table metadata
"""

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from phlo.cli.utils import get_iceberg_catalog

console = Console()


@click.group()
def catalog():
    """Manage Iceberg catalog and tables."""
    pass


@catalog.command()
@click.option(
    "--namespace",
    default=None,
    help="Filter by namespace (e.g., raw, bronze)",
)
@click.option(
    "--ref",
    default="main",
    help="Nessie branch/tag reference",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def tables(namespace: Optional[str], ref: str, format: str):
    """
    List all Iceberg tables in catalog.

    Shows namespace, table name, and location.

    Examples:
        phlo catalog tables
        phlo catalog tables --namespace raw
        phlo catalog tables --ref dev
        phlo catalog tables --format json
    """
    try:
        cat = get_iceberg_catalog(ref=ref)

        # Get all tables
        all_tables = []

        # List namespaces
        namespaces = cat.list_namespaces()

        for ns_tuple in namespaces:
            ns_name = ".".join(ns_tuple)

            # Filter by namespace if specified
            if namespace and namespace != ns_name:
                continue

            try:
                # List tables in namespace
                tables_in_ns = cat.list_tables(ns_name)
                for table_id in tables_in_ns:
                    all_tables.append({
                        "namespace": ns_name,
                        "table": table_id.name,
                        "full_name": str(table_id),
                    })
            except Exception as e:
                console.print(f"[yellow]Warning: Could not list tables in {ns_name}: {e}[/yellow]")

        if not all_tables:
            console.print("[yellow]No tables found[/yellow]")
            return

        if format == "json":
            click.echo(json.dumps(all_tables, indent=2))
        else:
            table = Table(title=f"Iceberg Tables (ref: {ref})")
            table.add_column("Namespace", style="cyan")
            table.add_column("Table Name", style="green")
            table.add_column("Full Name", style="dim")

            for row in sorted(all_tables, key=lambda x: x["full_name"]):
                table.add_row(
                    row["namespace"],
                    row["table"],
                    row["full_name"],
                )

            console.print(table)

            console.print(f"\n[dim]Total: {len(all_tables)} tables[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing tables: {e}[/red]")
        sys.exit(1)


@catalog.command()
@click.argument("table_name")
@click.option(
    "--ref",
    default="main",
    help="Nessie branch/tag reference",
)
def describe(table_name: str, ref: str):
    """
    Show detailed table metadata.

    Displays schema, partitioning, properties, and snapshot ID.

    Examples:
        phlo catalog describe raw.glucose_entries
        phlo catalog describe bronze.customer_data --ref dev
    """
    try:
        cat = get_iceberg_catalog(ref=ref)

        # Load table
        try:
            table = cat.load_table(table_name)
        except Exception as e:
            console.print(f"[red]Table not found: {table_name}[/red]")
            console.print(f"[yellow]Error: {e}[/yellow]")
            sys.exit(1)

        # Get metadata
        schema = table.schema()
        current_snapshot = table.current_snapshot()

        # Show basic info
        console.print(f"\n[bold blue]Table: {table_name}[/bold blue]")
        console.print(f"Location: {table.location()}")
        console.print(f"Current Snapshot ID: {current_snapshot.snapshot_id if current_snapshot else 'None'}")
        console.print(f"Format Version: {table.format_version()}")

        # Show schema
        console.print("\n[bold]Schema:[/bold]")
        schema_table = Table()
        schema_table.add_column("Column Name", style="cyan")
        schema_table.add_column("Type", style="green")
        schema_table.add_column("Required", justify="center")

        for field in schema.fields:
            required = "✓" if not field.type.is_optional else ""
            schema_table.add_row(field.name, str(field.type), required)

        console.print(schema_table)

        # Show partitioning
        spec = table.spec()
        if spec and spec.fields:
            console.print("\n[bold]Partitioning:[/bold]")
            part_table = Table()
            part_table.add_column("Field", style="cyan")
            part_table.add_column("Transform", style="green")

            for part_field in spec.fields:
                part_table.add_row(part_field.source_id, str(part_field.transform))

            console.print(part_table)

        # Show properties
        if table.properties():
            console.print("\n[bold]Properties:[/bold]")
            prop_table = Table()
            prop_table.add_column("Key", style="cyan")
            prop_table.add_column("Value", style="green")

            for key, value in sorted(table.properties().items()):
                prop_table.add_row(key, value)

            console.print(prop_table)

    except Exception as e:
        console.print(f"[red]Error describing table: {e}[/red]")
        sys.exit(1)


@catalog.command()
@click.argument("table_name")
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of snapshots to show",
)
@click.option(
    "--ref",
    default="main",
    help="Nessie branch/tag reference",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def history(table_name: str, limit: int, ref: str, format: str):
    """
    Show table snapshot history.

    Lists recent snapshots with timestamps and operations.

    Examples:
        phlo catalog history raw.glucose_entries
        phlo catalog history raw.glucose_entries --limit 50
        phlo catalog history raw.glucose_entries --ref dev
    """
    try:
        cat = get_iceberg_catalog(ref=ref)

        # Load table
        try:
            table = cat.load_table(table_name)
        except Exception:
            console.print(f"[red]Table not found: {table_name}[/red]")
            sys.exit(1)

        # Get snapshots
        snapshots = []
        current_snapshot = table.current_snapshot()

        # Traverse snapshot history
        snapshot_iter = table.history()
        for i, snapshot in enumerate(snapshot_iter):
            if i >= limit:
                break

            is_current = current_snapshot and snapshot.snapshot_id == current_snapshot.snapshot_id

            snapshots.append({
                "snapshot_id": snapshot.snapshot_id,
                "timestamp": snapshot.timestamp_ms,
                "operation": snapshot.operation,
                "summary": snapshot.summary,
                "is_current": is_current,
            })

        if not snapshots:
            console.print("[yellow]No snapshots found[/yellow]")
            return

        if format == "json":
            click.echo(json.dumps(snapshots, indent=2, default=str))
        else:
            table = Table(title=f"Snapshot History: {table_name}")
            table.add_column("Snapshot ID", style="cyan")
            table.add_column("Timestamp", style="green")
            table.add_column("Operation", style="magenta")
            table.add_column("Current", justify="center")

            for snapshot in snapshots:
                current_marker = "●" if snapshot["is_current"] else ""
                ts = snapshot["timestamp"]
                # Convert milliseconds to readable format
                from datetime import datetime
                ts_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

                table.add_row(
                    str(snapshot["snapshot_id"])[:8] + "...",
                    ts_str,
                    snapshot["operation"],
                    current_marker,
                )

            console.print(table)

            console.print(f"\n[dim]Showing {len(snapshots)} most recent snapshots[/dim]")

    except Exception as e:
        console.print(f"[red]Error retrieving history: {e}[/red]")
        sys.exit(1)
