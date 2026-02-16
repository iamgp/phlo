"""Logs Display

Rich formatting and display functions for log output.
"""

import json
import time
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.live import Live
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()


def _tail_logs(
    filters: dict,
    full: bool = False,
    output_json: bool = False,
) -> None:
    """
    Tail logs in real-time (follow mode).

    Args:
        filters: Filter criteria
        full: Whether to show full messages
        output_json: JSON output format
    """
    from phlo_dagster.cli_logs import _get_logs

    console.print("[yellow]Tailing logs (press Ctrl+C to stop)...[/yellow]\n")

    last_fetch_time = datetime.now(timezone.utc)
    seen_logs = set()

    def generate_logs_table():
        """Build a table for newly fetched log entries.

        Returns:
            Rich renderable containing log rows or an empty-state message.
        """
        nonlocal last_fetch_time

        # Fetch new logs
        filters["start_time"] = last_fetch_time
        logs_data = _get_logs(filters)
        last_fetch_time = datetime.now(timezone.utc)

        if not logs_data:
            return Text("[dim]No new logs...[/dim]")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Time", style="cyan", width=19)
        table.add_column("Level", style="white", width=8)
        table.add_column("Message", style="white")

        for log in logs_data:
            log_id = f"{log['timestamp']}-{log['message'][:20]}"
            if log_id in seen_logs:
                continue
            seen_logs.add(log_id)

            # Format timestamp
            try:
                ts = datetime.fromisoformat(log["timestamp"])
                time_str = ts.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = str(log["timestamp"])[:8]

            # Color-code level
            level = log["level"]
            if level == "ERROR":
                level_str = f"[red]{level}[/red]"
            elif level == "WARNING":
                level_str = f"[yellow]{level}[/yellow]"
            elif level == "DEBUG":
                level_str = f"[dim]{level}[/dim]"
            else:
                level_str = f"[green]{level}[/green]"

            # Truncate message
            message = log["message"]
            if not full and len(message) > 80:
                message = message[:77] + "..."

            table.add_row(time_str, level_str, message)

        return table if table.row_count > 0 else Text("[dim]No new logs...[/dim]")

    # Live display for real-time updates
    try:
        with Live(
            generate_logs_table(),
            refresh_per_second=0.5,
            console=console,
        ) as live:
            while True:
                live.update(generate_logs_table())
                time.sleep(2)  # Poll every 2 seconds
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped tailing logs[/yellow]")


def _display_logs(
    logs_data: list[dict],
    full: bool = False,
    output_json: bool = False,
) -> None:
    """
    Display logs in formatted output.

    Args:
        logs_data: List of log dictionaries
        full: Whether to show full messages
        output_json: JSON output format
    """
    if not logs_data:
        console.print("[yellow]No logs found[/yellow]")
        return

    if output_json:
        click.echo(json.dumps(logs_data, indent=2, default=str))
        return

    # Build table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Time", style="cyan", width=19)
    table.add_column("Level", style="white", width=8)
    table.add_column("Run ID", style="magenta", width=8)
    table.add_column("Job", style="white")
    table.add_column("Message", style="white")

    for log in logs_data:
        # Format timestamp
        try:
            ts = datetime.fromisoformat(log["timestamp"])
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            time_str = str(log["timestamp"])[:19]

        # Color-code level
        level = log["level"]
        if level == "ERROR":
            level_str = f"[red]{level}[/red]"
        elif level == "WARNING":
            level_str = f"[yellow]{level}[/yellow]"
        elif level == "DEBUG":
            level_str = f"[dim]{level}[/dim]"
        else:
            level_str = f"[green]{level}[/green]"

        # Truncate message
        message = log.get("message", "")
        if not full and len(message) > 80:
            message = message[:77] + "..."

        # Check if message contains JSON and syntax highlight
        if _is_json(message) and full:
            try:
                parsed = json.loads(message)
                message = Syntax(
                    json.dumps(parsed, indent=2),
                    "json",
                    theme="monokai",
                    line_numbers=False,
                )
            except json.JSONDecodeError:
                pass

        run_id = log.get("run_id", "-")[:8]
        job = log.get("job_name", "-")[:20]

        table.add_row(time_str, level_str, run_id, job, message)

    console.print(table)
    console.print(f"\n[dim]Total: {len(logs_data)} logs[/dim]")


def _is_json(text: str) -> bool:
    """Check if text is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError, ValueError):
        return False
