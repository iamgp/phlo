"""CLI commands for lineage visualization and analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phlo_lineage import get_lineage_graph

console = Console()


def _resolve_asset_name(graph, asset_name: str) -> tuple[str | None, list[str]]:
    """Resolve a user-provided asset name to a known asset key.

    Returns a tuple of (resolved_name, matches). If resolved_name is None,
    matches contains candidate asset keys (possibly empty).
    """
    if asset_name in graph.assets:
        return asset_name, [asset_name]

    normalized = asset_name.replace("/", ".")
    if normalized in graph.assets:
        return normalized, [normalized]

    query_segments = [seg for seg in re.split(r"[./]", asset_name) if seg]
    matches: list[str] = []
    for name in graph.assets.keys():
        name_segments = [seg for seg in re.split(r"[./]", name) if seg]
        if (
            len(name_segments) >= len(query_segments)
            and name_segments[-len(query_segments) :] == query_segments
        ):
            matches.append(name)

    if len(matches) == 1:
        return matches[0], matches

    return None, matches


@click.group(name="lineage")
def lineage_group():
    """Asset dependency and lineage visualization."""
    pass


@lineage_group.command(name="show")
@click.argument("asset_name")
@click.option(
    "--direction",
    type=click.Choice(["upstream", "downstream", "both"]),
    default="both",
    help="Direction to show (default: both)",
)
@click.option(
    "--depth",
    type=int,
    default=None,
    help="Maximum depth to traverse",
)
def show_lineage(asset_name: str, direction: str, depth: Optional[int]) -> None:
    """
    Display asset dependencies in ASCII tree format.

    Shows upstream dependencies and downstream dependents.

    Examples:
        phlo lineage show glucose_entries
        phlo lineage show glucose_entries --upstream
        phlo lineage show glucose_entries --downstream --depth 2
    """
    graph = get_lineage_graph()

    resolved_name, matches = _resolve_asset_name(graph, asset_name)
    if not resolved_name:
        console.print(f"[yellow]⚠[/yellow]  Asset '{asset_name}' not found in lineage graph")
        if matches:
            console.print("\nPossible matches:")
            for name in sorted(matches):
                asset = graph.assets[name]
                console.print(
                    f"  • {name} ({asset.asset_type})",
                    style="cyan" if asset.status == "success" else "red",
                )
        else:
            console.print("\nAvailable assets:")
            for name in sorted(graph.assets.keys()):
                asset = graph.assets[name]
                console.print(
                    f"  • {name} ({asset.asset_type})",
                    style="cyan" if asset.status == "success" else "red",
                )
        return

    # Generate ASCII tree
    tree = graph.to_ascii_tree(resolved_name, direction=direction, depth=depth)

    # Display with panel
    title = f"Lineage: {resolved_name}"
    if depth:
        title += f" (depth ≤ {depth})"

    console.print(Panel(tree, title=title, expand=False))


@lineage_group.command(name="export")
@click.argument("asset_name")
@click.option(
    "--format",
    type=click.Choice(["dot", "mermaid", "json"]),
    default="dot",
    help="Export format",
)
@click.option(
    "--output",
    type=Path,
    required=True,
    help="Output file path",
)
def export_lineage(asset_name: str, format: str, output: Path) -> None:
    """
    Export lineage to external formats.

    Supports Graphviz DOT, Mermaid diagram, and JSON formats.

    Examples:
        phlo lineage export glucose_entries --format dot --output lineage.dot
        phlo lineage export glucose_entries --format mermaid --output lineage.md
        phlo lineage export glucose_entries --format json --output lineage.json
    """
    graph = get_lineage_graph()

    if not graph.assets:
        console.print("[red]✗[/red] Lineage graph is empty")
        return

    # Export based on format
    if format == "dot":
        content = graph.to_dot()
    elif format == "mermaid":
        content = graph.to_mermaid()
    elif format == "json":
        content = graph.to_json()
    else:
        console.print(f"[red]✗[/red] Unknown format: {format}")
        return

    # Write to file
    with open(output, "w") as f:
        f.write(content)

    console.print(f"[green]✓[/green] Lineage exported to {output}")

    # Show preview
    if format == "dot":
        console.print(
            "\n[dim]Tip: Render with Graphviz:[/dim] "
            "[cyan]dot -Tpng lineage.dot -o lineage.png[/cyan]"
        )
    elif format == "mermaid":
        console.print("\n[dim]Tip: View in GitHub markdown or Mermaid Live Editor[/dim]")


@lineage_group.command(name="impact")
@click.argument("asset_name")
def analyze_impact(asset_name: str) -> None:
    """
    Analyze downstream impact of an asset.

    Shows which assets would be affected by a failure or change
    to the specified asset.

    Examples:
        phlo lineage impact glucose_entries
        phlo lineage impact stg_glucose_entries
    """
    graph = get_lineage_graph()

    resolved_name, matches = _resolve_asset_name(graph, asset_name)
    if not resolved_name:
        console.print(f"[yellow]⚠[/yellow]  Asset '{asset_name}' not found in lineage graph")
        if matches:
            console.print("\nPossible matches:")
            for name in sorted(matches):
                console.print(f"  • {name}")
        return

    impact = graph.get_impact(resolved_name)

    # Display impact analysis
    console.print(f"\n[bold]Impact Analysis: {resolved_name}[/bold]\n")

    console.print(f"Directly Affected: {impact['direct_count']} asset(s)")
    console.print(f"Indirectly Affected: {impact['indirect_count']} asset(s)")
    console.print(
        f"Publishing Assets Affected: {'[red]Yes[/red]' if impact['publishing_affected'] else '[green]No[/green]'}"
    )

    if impact["affected_assets"]:
        console.print(f"\n[bold]Affected Assets ({len(impact['affected_assets'])} total):[/bold]")
        for asset in sorted(impact["affected_assets"]):
            asset_obj = graph.assets.get(asset)
            console.print(f"  • {asset} ({asset_obj.asset_type if asset_obj else 'unknown'})")

    if impact["publishing_affected"]:
        console.print("\n[bold red]⚠ WARNING:[/bold red] This change would affect published data!")


@lineage_group.command(name="status")
def lineage_status() -> None:
    """Show lineage graph status and statistics."""
    graph = get_lineage_graph()

    console.print("[bold]Lineage Graph Status[/bold]\n")

    # Statistics
    asset_count = len(graph.assets)
    edge_count = sum(len(targets) for targets in graph.edges.values())

    console.print(f"Total Assets: {asset_count}")
    console.print(f"Total Dependencies: {edge_count}")

    # Count by type
    type_counts = {}
    for asset in graph.assets.values():
        type_counts[asset.asset_type] = type_counts.get(asset.asset_type, 0) + 1

    if type_counts:
        console.print("\n[bold]Assets by Type:[/bold]")
        for asset_type, count in sorted(type_counts.items()):
            console.print(f"  • {asset_type}: {count}")

    # Count by status
    status_counts = {}
    for asset in graph.assets.values():
        status_counts[asset.status] = status_counts.get(asset.status, 0) + 1

    if status_counts:
        console.print("\n[bold]Assets by Status:[/bold]")
        for status, count in sorted(status_counts.items()):
            console.print(f"  • {status}: {count}")


@lineage_group.group(name="column")
def column_group():
    """Column-level lineage commands."""
    pass


@column_group.command(name="import-dbt")
@click.option(
    "--manifest",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to dbt manifest.json",
)
def import_dbt(manifest: Path) -> None:
    """Import column lineage from a dbt manifest.json.

    Uses same-name heuristic matching between upstream and downstream
    model columns.

    Examples:
        phlo lineage column import-dbt --manifest target/manifest.json
    """
    from phlo_lineage.dbt_column_lineage import extract_column_lineage
    from phlo_lineage.store import LineageStore, resolve_lineage_db_url

    with open(manifest) as f:
        manifest_data = json.load(f)

    mappings = extract_column_lineage(manifest_data)

    if not mappings:
        console.print("[yellow]⚠[/yellow]  No column lineage mappings found in manifest")
        return

    connection_string = resolve_lineage_db_url()
    if not connection_string:
        console.print("[red]✗[/red]  No lineage database configured")
        return

    store = LineageStore(connection_string)
    count = store.record_column_lineage(mappings)
    console.print(f"[green]✓[/green]  Imported {count} column lineage mapping(s)")


@column_group.command(name="upstream")
@click.argument("asset")
@click.option("--column", default=None, help="Filter to a specific column")
def column_upstream(asset: str, column: str | None) -> None:
    """Show upstream column lineage for an asset.

    Examples:
        phlo lineage column upstream silver.stg_glucose
        phlo lineage column upstream silver.stg_glucose --column glucose_value
    """
    from phlo_lineage.store import LineageStore, resolve_lineage_db_url

    connection_string = resolve_lineage_db_url()
    if not connection_string:
        console.print("[red]✗[/red]  No lineage database configured")
        return

    store = LineageStore(connection_string)
    results = store.get_upstream_columns(asset, target_column=column)

    if not results:
        console.print("[yellow]⚠[/yellow]  No upstream column lineage found")
        return

    table = Table(title=f"Upstream columns for {asset}")
    table.add_column("Source Asset", style="cyan")
    table.add_column("Source Column", style="green")
    table.add_column("Target Column", style="green")
    table.add_column("Source Type", style="dim")

    for r in results:
        table.add_row(r.source_asset, r.source_column, r.target_column, r.source_type)

    console.print(table)


@column_group.command(name="downstream")
@click.argument("asset")
@click.option("--column", default=None, help="Filter to a specific column")
def column_downstream(asset: str, column: str | None) -> None:
    """Show downstream column lineage for an asset.

    Examples:
        phlo lineage column downstream bronze.dlt_glucose
        phlo lineage column downstream bronze.dlt_glucose --column glucose_value
    """
    from phlo_lineage.store import LineageStore, resolve_lineage_db_url

    connection_string = resolve_lineage_db_url()
    if not connection_string:
        console.print("[red]✗[/red]  No lineage database configured")
        return

    store = LineageStore(connection_string)
    results = store.get_downstream_columns(asset, source_column=column)

    if not results:
        console.print("[yellow]⚠[/yellow]  No downstream column lineage found")
        return

    table = Table(title=f"Downstream columns for {asset}")
    table.add_column("Target Asset", style="cyan")
    table.add_column("Target Column", style="green")
    table.add_column("Source Column", style="green")
    table.add_column("Source Type", style="dim")

    for r in results:
        table.add_row(r.target_asset, r.target_column, r.source_column, r.source_type)

    console.print(table)


if __name__ == "__main__":
    lineage_group()
