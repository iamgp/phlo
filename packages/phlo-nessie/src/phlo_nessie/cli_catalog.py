"""
Catalog CLI commands.

This CLI is intentionally shipped with `phlo-nessie` because Nessie is the current catalog backend.

Implementation uses `phlo-iceberg` (PyIceberg + Nessie REST catalog) when available.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_iceberg_catalog(ref: str = "main"):
    try:
        from phlo_iceberg.catalog import get_catalog
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Iceberg catalog support is not installed. Install `phlo-iceberg` (or `phlo[defaults]`)."
        ) from exc

    return get_catalog(ref=ref)


@click.group()
def catalog():
    """Manage the lakehouse catalog (Nessie-backed)."""


@catalog.command()
@click.option("--namespace", default=None, help="Filter by namespace (e.g., raw, bronze)")
@click.option("--ref", default="main", help="Nessie branch/tag reference")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
def tables(namespace: Optional[str], ref: str, output_format: str) -> None:
    """List all Iceberg tables in the catalog."""
    try:
        cat = _get_iceberg_catalog(ref=ref)

        all_tables: list[dict[str, str]] = []
        for ns_tuple in cat.list_namespaces():
            ns_name = ".".join(ns_tuple)
            if namespace and namespace != ns_name:
                continue
            try:
                for table_id in cat.list_tables(ns_name):
                    all_tables.append(
                        {
                            "namespace": ns_name,
                            "table": table_id[-1] if isinstance(table_id, tuple) else str(table_id),
                            "full_name": ".".join(table_id) if isinstance(table_id, tuple) else str(table_id),
                        }
                    )
            except Exception as e:
                console.print(f"[yellow]Warning: Could not list tables in {ns_name}: {e}[/yellow]")

        if not all_tables:
            console.print("[yellow]No tables found[/yellow]")
            return

        if output_format == "json":
            click.echo(json.dumps(all_tables, indent=2))
            return

        table = Table(title=f"Iceberg Tables (ref: {ref})")
        table.add_column("Namespace", style="cyan")
        table.add_column("Table Name", style="green")
        table.add_column("Full Name", style="dim")

        for row in sorted(all_tables, key=lambda x: x["full_name"]):
            table.add_row(row["namespace"], row["table"], row["full_name"])

        console.print(table)
        console.print(f"\n[dim]Total: {len(all_tables)} tables[/dim]")
    except Exception as e:
        console.print(f"[red]Error listing tables: {e}[/red]")
        sys.exit(1)


@catalog.command()
@click.argument("table_name")
@click.option("--ref", default="main", help="Nessie branch/tag reference")
def describe(table_name: str, ref: str) -> None:
    """Show detailed table metadata."""
    try:
        cat = _get_iceberg_catalog(ref=ref)
        try:
            table = cat.load_table(table_name)
        except Exception as e:
            console.print(f"[red]Table not found: {table_name}[/red]")
            console.print(f"[yellow]Error: {e}[/yellow]")
            sys.exit(1)

        schema = table.schema()
        current_snapshot = table.current_snapshot()

        console.print(f"\n[bold blue]Table: {table_name}[/bold blue]")
        console.print(f"Location: {table.location()}")
        console.print(
            f"Current Snapshot ID: {current_snapshot.snapshot_id if current_snapshot else 'None'}"
        )
        console.print(f"Format Version: {table.format_version()}")

        console.print("\n[bold]Schema:[/bold]")
        schema_table = Table()
        schema_table.add_column("Column Name", style="cyan")
        schema_table.add_column("Type", style="green")
        schema_table.add_column("Required", justify="center")

        for field in schema.fields:
            required = "✓" if not field.type.is_optional else ""
            schema_table.add_row(field.name, str(field.type), required)
        console.print(schema_table)

        spec = table.spec()
        if spec and spec.fields:
            console.print("\n[bold]Partitioning:[/bold]")
            part_table = Table()
            part_table.add_column("Field", style="cyan")
            part_table.add_column("Transform", style="green")
            for part_field in spec.fields:
                part_table.add_row(str(part_field.source_id), str(part_field.transform))
            console.print(part_table)

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
@click.option("--limit", type=int, default=10, help="Number of snapshots to show")
@click.option("--ref", default="main", help="Nessie branch/tag reference")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
def history(table_name: str, limit: int, ref: str, output_format: str) -> None:
    """Show table snapshot history."""
    try:
        cat = _get_iceberg_catalog(ref=ref)
        try:
            table = cat.load_table(table_name)
        except Exception:
            console.print(f"[red]Table not found: {table_name}[/red]")
            sys.exit(1)

        snapshots = []
        for snapshot in table.snapshots():
            summary = snapshot.summary or {}
            snapshots.append(
                {
                    "id": snapshot.snapshot_id,
                    "timestamp": snapshot.timestamp_ms,
                    "operation": summary.get("operation", ""),
                    "added_files": summary.get("added-data-files", ""),
                    "removed_files": summary.get("deleted-data-files", ""),
                }
            )

        snapshots = sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)[:limit]

        if output_format == "json":
            click.echo(json.dumps(snapshots, indent=2))
            return

        table_out = Table(title=f"Snapshot History: {table_name} (ref: {ref})")
        table_out.add_column("Snapshot ID", style="cyan")
        table_out.add_column("Timestamp (ms)", style="green")
        table_out.add_column("Operation")
        table_out.add_column("Added Files")
        table_out.add_column("Removed Files")

        for s in snapshots:
            table_out.add_row(
                str(s["id"]),
                str(s["timestamp"]),
                str(s["operation"]),
                str(s["added_files"]),
                str(s["removed_files"]),
            )

        console.print(table_out)
    except Exception as e:
        console.print(f"[red]Error showing history: {e}[/red]")
        sys.exit(1)
