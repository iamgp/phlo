"""Backfill Command

Run asset materialization across a date range with parallel execution.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from phlo.cli.services import find_dagster_container, get_project_name

console = Console()


@click.command()
@click.argument("asset_name", required=False)
@click.option(
    "--start-date",
    type=str,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=str,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--partitions",
    type=str,
    help="Comma-separated partition dates (YYYY-MM-DD,YYYY-MM-DD,...)",
)
@click.option(
    "--parallel",
    type=int,
    default=1,
    help="Number of concurrent partitions to process (default: 1)",
)
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Resume last backfill, skipping completed partitions",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be executed without running",
)
@click.option(
    "--delay",
    type=float,
    default=0.0,
    help="Delay between parallel executions in seconds (rate limiting)",
)
def backfill(
    asset_name: str | None,
    start_date: str | None,
    end_date: str | None,
    partitions: str | None,
    parallel: int,
    resume: bool,
    dry_run: bool,
    delay: float,
):
    """
    Run asset materialization across a date range with parallel execution.

    Supports multiple invocation modes:
    - Date range: --start-date and --end-date
    - Explicit partitions: --partitions comma-separated
    - Resume: --resume to continue interrupted backfill

    \b
    Examples:
      phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31
      phlo backfill glucose_entries --partitions 2024-01-01,2024-01-15,2024-01-31
      phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-12-31 --parallel 4
      phlo backfill --resume
      phlo backfill glucose_entries --start-date 2024-01-01 --end-date 2024-01-31 --dry-run
    """
    console.print("\n[bold blue]📦 Asset Backfill[/bold blue]\n")

    # Validate inputs
    if resume:
        # Resume mode: load from state file
        state_file = Path(".phlo/backfill_state.json")
        if not state_file.exists():
            click.echo(
                "Error: No backfill state found. Cannot resume.",
                err=True,
            )
            sys.exit(1)

        try:
            state = json.loads(state_file.read_text())
            asset_name = state.get("asset_name")
            partition_dates = state.get("remaining_partitions", [])
            completed_partitions = state.get("completed_partitions", [])
        except Exception as e:
            click.echo(f"Error reading backfill state: {e}", err=True)
            sys.exit(1)
    else:
        # Determine partition list
        if partitions:
            # Explicit partitions
            partition_dates = [p.strip() for p in partitions.split(",")]
            _validate_partition_dates(partition_dates)
        elif start_date and end_date:
            # Generate from date range
            partition_dates = _generate_partition_dates(start_date, end_date)
        else:
            click.echo(
                "Error: Must specify either --start-date/--end-date or --partitions",
                err=True,
            )
            sys.exit(1)

        if not asset_name:
            click.echo("Error: Asset name is required", err=True)
            sys.exit(1)

        completed_partitions = []

    # Validate asset name
    if not asset_name:
        click.echo("Error: Asset name is required", err=True)
        sys.exit(1)

    # Validate parallel value
    if parallel < 1:
        click.echo(
            "Error: Parallel must be >= 1",
            err=True,
        )
        sys.exit(1)

    # Display backfill plan
    console.print(f"[cyan]Asset:[/cyan] {asset_name}")
    console.print(f"[cyan]Total partitions:[/cyan] {len(partition_dates)}")
    console.print(f"[cyan]Parallel workers:[/cyan] {parallel}")

    if completed_partitions:
        console.print(f"[yellow]Already completed:[/yellow] {len(completed_partitions)}")
        console.print(f"[yellow]Remaining:[/yellow] {len(partition_dates)}")

    if dry_run:
        console.print("\n[yellow]Dry run - showing first 5 commands:[/yellow]\n")
        for date in partition_dates[:5]:
            cmd = _build_materialize_command(asset_name, date)
            console.print(f"[dim]{' '.join(cmd)}[/dim]")
        if len(partition_dates) > 5:
            console.print(f"[dim]... and {len(partition_dates) - 5} more[/dim]")
        return

    if not partition_dates:
        console.print("[yellow]No partitions to backfill[/yellow]")
        return

    # Run backfill with progress tracking
    console.print()
    _run_backfill(
        asset_name,
        partition_dates,
        parallel=parallel,
        delay=delay,
        completed_partitions=completed_partitions,
    )


def _generate_partition_dates(start_date: str, end_date: str) -> list[str]:
    """
    Generate list of partition dates for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        click.echo(
            "Error: Invalid date format. Use YYYY-MM-DD",
            err=True,
        )
        sys.exit(1)

    if start > end:
        click.echo(
            "Error: Start date must be before end date",
            err=True,
        )
        sys.exit(1)

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def _validate_partition_dates(dates: list[str]) -> None:
    """
    Validate partition date format.

    Args:
        dates: List of date strings to validate

    Raises:
        SystemExit if validation fails
    """
    for date in dates:
        try:
            datetime.strptime(date.strip(), "%Y-%m-%d")
        except ValueError:
            click.echo(
                f"Error: Invalid partition date: {date}. Use YYYY-MM-DD",
                err=True,
            )
            sys.exit(1)


def _build_materialize_command(asset_name: str, partition_date: str) -> list[str]:
    """
    Build the docker exec command for materializing an asset.

    Args:
        asset_name: Name of the asset to materialize
        partition_date: Partition date in YYYY-MM-DD format

    Returns:
        List of command components
    """
    import platform

    project_name = get_project_name()
    container_name = find_dagster_container(project_name)
    host_platform = platform.system()

    return [
        "docker",
        "exec",
        "-e",
        f"CASCADE_HOST_PLATFORM={host_platform}",
        "-w",
        "/app",
        container_name,
        "dagster",
        "asset",
        "materialize",
        "-m",
        "phlo.framework.definitions",
        "--select",
        asset_name,
        "--partition",
        partition_date,
    ]


def _run_backfill(
    asset_name: str,
    partition_dates: list[str],
    parallel: int = 1,
    delay: float = 0.0,
    completed_partitions: list[str] | None = None,
) -> None:
    """
    Execute backfill with progress tracking.

    Args:
        asset_name: Asset to backfill
        partition_dates: List of partition dates
        parallel: Number of concurrent workers
        delay: Delay between executions in seconds
        completed_partitions: List of already-completed partitions
    """
    if completed_partitions is None:
        completed_partitions = []

    # Filter out completed partitions
    remaining = [d for d in partition_dates if d not in completed_partitions]
    total = len(partition_dates)
    already_done = len(completed_partitions)

    results = {
        "asset_name": asset_name,
        "start_time": datetime.utcnow().isoformat(),
        "total_partitions": total,
        "completed_partitions": completed_partitions,
        "successful": [],
        "failed": [],
    }

    # Use ThreadPoolExecutor for parallel execution
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]Backfilling {asset_name}...", total=total)

        with ThreadPoolExecutor(max_workers=parallel) as executor:
            # Submit all tasks
            future_to_date = {
                executor.submit(
                    _materialize_partition,
                    asset_name,
                    date,
                    delay if i > 0 else 0,
                ): date
                for i, date in enumerate(remaining)
            }

            # Process completed tasks
            completed_count = already_done
            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    success, output = future.result()
                    if success:
                        results["successful"].append(date)
                        completed_count += 1
                        progress.update(
                            task,
                            completed=completed_count,
                            description=f"[green]✓ Completed {completed_count}/{total}[/green]",
                        )
                    else:
                        results["failed"].append({"date": date, "error": output})
                        progress.update(
                            task,
                            description=f"[yellow]⚠ Failed {date}[/yellow]",
                        )
                except Exception as e:
                    results["failed"].append({"date": date, "error": str(e)})
                    progress.update(
                        task,
                        description=f"[red]✗ Error {date}[/red]",
                    )

                # Update state file periodically
                _save_backfill_state(asset_name, remaining, results["successful"])

    # Display results
    console.print()
    _display_backfill_results(results)

    # Clean up state file on success
    if not results["failed"]:
        state_file = Path(".phlo/backfill_state.json")
        if state_file.exists():
            state_file.unlink()
    else:
        # Save final state for resume
        remaining_after = [d for d in partition_dates if d not in results["successful"]]
        _save_backfill_state(asset_name, remaining_after, results["successful"])


def _materialize_partition(
    asset_name: str,
    partition_date: str,
    delay: float = 0.0,
) -> tuple[bool, str]:
    """
    Materialize a single partition.

    Args:
        asset_name: Asset to materialize
        partition_date: Partition date
        delay: Delay before execution in seconds

    Returns:
        Tuple of (success, output_message)
    """
    import time

    if delay > 0:
        time.sleep(delay)

    cmd = _build_materialize_command(asset_name, partition_date)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per partition
        )

        if result.returncode == 0:
            return True, f"Materialized {partition_date}"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, f"Timeout after 1 hour for partition {partition_date}"
    except FileNotFoundError:
        return False, "Docker not found or container not running"
    except Exception as e:
        return False, str(e)


def _save_backfill_state(
    asset_name: str,
    remaining_partitions: list[str],
    completed_partitions: list[str],
) -> None:
    """
    Save backfill state for resume capability.

    Args:
        asset_name: Asset name
        remaining_partitions: Partitions still to process
        completed_partitions: Completed partitions
    """
    state_dir = Path(".phlo")
    state_dir.mkdir(exist_ok=True)

    state = {
        "asset_name": asset_name,
        "remaining_partitions": remaining_partitions,
        "completed_partitions": completed_partitions,
        "last_updated": datetime.utcnow().isoformat(),
    }

    state_file = state_dir / "backfill_state.json"
    state_file.write_text(json.dumps(state, indent=2))


def _display_backfill_results(results: dict[str, any]) -> None:
    """
    Display backfill results in a formatted table.

    Args:
        results: Backfill results dictionary
    """
    successful = len(results["successful"])
    failed = len(results["failed"])
    total = results["total_partitions"]

    console.print("[bold blue]Backfill Results[/bold blue]\n")

    # Summary
    table = Table(show_header=False)
    table.add_row("[cyan]Asset[/cyan]", results["asset_name"])
    table.add_row(
        "[cyan]Status[/cyan]",
        "[green]✓ Success[/green]" if failed == 0 else "[yellow]⚠ Partial[/yellow]",
    )
    table.add_row("[cyan]Completed[/cyan]", f"[green]{successful}[/green]")
    table.add_row("[cyan]Failed[/cyan]", f"[red]{failed}[/red]" if failed > 0 else "0")
    table.add_row("[cyan]Total[/cyan]", str(total))

    console.print(table)

    # Show failures if any
    if results["failed"]:
        console.print("\n[bold yellow]Failed Partitions[/bold yellow]\n")
        fail_table = Table(show_header=True, header_style="bold")
        fail_table.add_column("Date", style="cyan")
        fail_table.add_column("Error", style="red")

        for item in results["failed"]:
            if isinstance(item, dict):
                date = item.get("date", "unknown")
                error = item.get("error", "unknown error")
            else:
                date = item
                error = "unknown"

            fail_table.add_row(date, error[:100])

        console.print(fail_table)

        console.print("\n[yellow]To resume, run: phlo backfill --resume[/yellow]")
        sys.exit(1)

    console.print("\n[green]✓ Backfill complete![/green]")
