"""CLI commands for metrics exposure and analysis."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phlo.metrics import get_metrics_collector

console = Console()


@click.group(name="metrics")
def metrics_group():
    """Pipeline and data metrics exposure."""
    pass


@metrics_group.command(name="summary")
@click.option(
    "--period",
    type=str,
    default="24h",
    help="Time period to analyze (e.g., 24h, 7d, 30d)",
)
def metrics_summary(period: str) -> None:
    """
    Show key metrics overview.

    Displays:
    - Total runs (24h): success/failure count
    - Data volume: rows processed, bytes written
    - Latency: p50, p95, p99 execution times
    - Active assets: count by status
    """
    # Parse period
    period_hours = _parse_period(period)

    collector = get_metrics_collector()
    metrics = collector.collect_summary(period_hours)

    # Build summary panel
    summary_text = f"""
[bold]Platform Metrics Summary[/bold]

[cyan]Runs (last {period})[/cyan]
  Total:     {metrics.total_runs_24h}
  Success:   {metrics.successful_runs_24h} ({_percentage(metrics.successful_runs_24h, metrics.total_runs_24h)}%)
  Failure:   {metrics.failed_runs_24h} ({_percentage(metrics.failed_runs_24h, metrics.total_runs_24h)}%)

[cyan]Data Volume[/cyan]
  Rows:      {_format_number(metrics.total_rows_processed_24h)}
  Bytes:     {_format_bytes(metrics.total_bytes_written_24h)}

[cyan]Latency (seconds)[/cyan]
  p50:       {metrics.p50_duration_seconds:.2f}s
  p95:       {metrics.p95_duration_seconds:.2f}s
  p99:       {metrics.p99_duration_seconds:.2f}s

[cyan]Assets[/cyan]
  Active:    {metrics.active_assets_count}
  Success:   {metrics.assets_by_status.get("success", 0)}
  Warning:   {metrics.assets_by_status.get("warning", 0)}
  Failure:   {metrics.assets_by_status.get("failure", 0)}
"""

    console.print(Panel(summary_text, title="📊 Metrics Summary", expand=False))


@metrics_group.command(name="asset")
@click.argument("asset_name")
@click.option(
    "--runs",
    type=int,
    default=10,
    help="Number of past runs to display",
)
def metrics_asset(asset_name: str, runs: int) -> None:
    """
    Show per-asset metrics.

    Displays:
    - Last 10 run durations
    - Average rows per run
    - Failure rate
    - Data growth trend
    """
    collector = get_metrics_collector()
    metrics = collector.collect_asset(asset_name, runs=runs)

    # Build asset metrics table
    table = Table(title=f"Metrics for {asset_name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Last Run Status", metrics.last_run.status if metrics.last_run else "-")
    table.add_row(
        "Last Run Duration",
        f"{metrics.last_run.duration_seconds:.2f}s"
        if metrics.last_run and metrics.last_run.duration_seconds
        else "-",
    )
    table.add_row("Average Duration", f"{metrics.average_duration:.2f}s")
    table.add_row("Failure Rate", f"{metrics.failure_rate:.1%}")
    table.add_row("Avg Rows/Run", f"{metrics.average_rows_per_run:,.0f}")
    table.add_row("Data Size", _format_bytes(metrics.data_growth_bytes))

    console.print(table)

    # Display run history
    if metrics.last_10_runs:
        console.print()
        run_table = Table(title=f"Last {len(metrics.last_10_runs)} Runs")
        run_table.add_column("Run ID", style="cyan")
        run_table.add_column("Status", style="magenta")
        run_table.add_column("Duration", style="yellow")
        run_table.add_column("Rows", style="green")

        for run in metrics.last_10_runs:
            status_color = "green" if run.status == "success" else "red"
            duration_str = f"{run.duration_seconds:.2f}s" if run.duration_seconds else "-"
            run_table.add_row(
                run.run_id[:8],
                f"[{status_color}]{run.status}[/{status_color}]",
                duration_str,
                f"{run.rows_processed:,}",
            )

        console.print(run_table)


@metrics_group.command(name="export")
@click.option(
    "--format",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    type=Path,
    required=True,
    help="Output file path",
)
@click.option(
    "--period",
    type=str,
    default="24h",
    help="Time period to analyze (e.g., 24h, 7d, 30d)",
)
def metrics_export(format: str, output: Path, period: str) -> None:
    """
    Export metrics to JSON or CSV.

    Useful for external analysis and integration with other tools.
    """
    period_hours = _parse_period(period)
    collector = get_metrics_collector()
    metrics = collector.collect_summary(period_hours)

    if format == "json":
        _export_json(metrics, output)
    elif format == "csv":
        _export_csv(metrics, output)

    console.print(f"[green]✓[/green] Metrics exported to {output}")


def _parse_period(period_str: str) -> int:
    """Parse period string to hours."""
    period_str = period_str.strip()

    if period_str.endswith("h"):
        try:
            return int(period_str[:-1])
        except ValueError:
            return 24
    elif period_str.endswith("d"):
        try:
            return int(period_str[:-1]) * 24
        except ValueError:
            return 24
    elif period_str.endswith("w"):
        try:
            return int(period_str[:-1]) * 24 * 7
        except ValueError:
            return 24
    else:
        return 24  # default


def _percentage(part: int, total: int) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def _format_number(num: int) -> str:
    """Format large numbers with commas."""
    return f"{num:,}"


def _format_bytes(bytes_val: int | float) -> str:
    """Format bytes as human-readable size."""
    val = float(bytes_val)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if val < 1024:
            return f"{val:.2f} {unit}"
        val /= 1024
    return f"{val:.2f} PB"


def _export_json(metrics: object, output: Path) -> None:
    """Export metrics as JSON."""
    # Convert dataclass to dict
    result = _dataclass_to_dict(metrics)
    if isinstance(result, dict):
        result["exported_at"] = datetime.utcnow().isoformat()
        with open(output, "w") as f:
            json.dump(result, f, indent=2, default=str)
    else:
        with open(output, "w") as f:
            json.dump({"data": result, "exported_at": datetime.utcnow().isoformat()}, f, indent=2, default=str)


def _export_csv(metrics: object, output: Path) -> None:
    """Export metrics as CSV."""
    import csv

    result = _dataclass_to_dict(metrics)
    if isinstance(result, dict):
        result["exported_at"] = datetime.utcnow().isoformat()
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=result.keys())
            writer.writeheader()
            writer.writerow(result)
    else:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["data", "exported_at"])
            writer.writerow([str(result), datetime.utcnow().isoformat()])


def _dataclass_to_dict(obj: object) -> dict | object:
    """Recursively convert dataclass to dict."""
    if hasattr(obj, "__dataclass_fields__"):
        result: dict = {}
        for field in obj.__dataclass_fields__:  # type: ignore[attr-defined]
            value = getattr(obj, field)
            if hasattr(value, "__dataclass_fields__"):
                result[field] = _dataclass_to_dict(value)
            elif isinstance(value, dict):
                result[field] = {k: _dataclass_to_dict(v) for k, v in value.items()}
            elif isinstance(value, list):
                result[field] = [
                    _dataclass_to_dict(item) if hasattr(item, "__dataclass_fields__") else item
                    for item in value
                ]
            else:
                result[field] = value
        return result
    return obj


if __name__ == "__main__":
    metrics_group()
