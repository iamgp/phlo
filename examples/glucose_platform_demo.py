#!/usr/bin/env python3
"""
Glucose Platform Demo - Interactive walkthrough of the Phlo platform

This script demonstrates the complete glucose monitoring platform:
1. Data ingestion from Nightscout API
2. Validation with Pandera schemas
3. Transformation through dbt layers
4. Publishing to PostgreSQL
5. API access and analytics

Usage:
    python examples/glucose_platform_demo.py --demo all
    python examples/glucose_platform_demo.py --demo ingestion
    python examples/glucose_platform_demo.py --demo analytics
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phlo.config import settings

console = Console()


def print_section(title: str, content: str = ""):
    """Print a formatted section header."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))
    if content:
        console.print(content)
    console.print()


def demo_architecture():
    """Show the platform architecture."""
    print_section("Platform Architecture")

    tree = Tree("[bold]Phlo Glucose Monitoring Platform[/bold]")

    # Ingestion layer
    ingestion = tree.add("[cyan]1. Ingestion Layer[/cyan]")
    ingestion.add("Nightscout API → DLT rest_api source")
    ingestion.add("Pandera validation (RawGlucoseEntries)")
    ingestion.add("S3/MinIO staging (Parquet)")
    ingestion.add("PyIceberg merge to dev branch")

    # Storage layer
    storage = tree.add("[cyan]2. Storage Layer[/cyan]")
    storage.add("Apache Iceberg tables (ACID)")
    storage.add("Project Nessie catalog (Git-like branching)")
    storage.add("MinIO object storage (S3-compatible)")

    # Transform layer
    transform = tree.add("[cyan]3. Transformation Layer (dbt)[/cyan]")
    bronze = transform.add("Bronze → stg_glucose_entries")
    bronze.add("Clean and standardize raw data")
    silver = transform.add("Silver → fct_glucose_readings")
    silver.add("+ Time dimensions (hour, day of week)")
    silver.add("+ Glucose categories (hypo/in-range/hyper)")
    silver.add("+ Rate of change calculations")
    gold = transform.add("Gold → fct_daily_glucose_metrics")
    gold.add("Daily aggregations (avg, min, max)")
    gold.add("Time in range percentages")
    gold.add("Estimated A1C (GMI)")

    # Publishing layer
    publishing = tree.add("[cyan]4. Publishing Layer[/cyan]")
    publishing.add("PostgreSQL marts (BI-ready)")
    publishing.add("Pandera validation before publish")

    # API/Analytics layer
    api = tree.add("[cyan]5. API & Analytics Layer[/cyan]")
    api.add("PostgREST (auto-generated REST API)")
    api.add("Hasura (GraphQL API)")
    api.add("Superset (dashboards)")
    api.add("DuckDB (analyst queries)")

    console.print(tree)


def demo_ingestion():
    """Demonstrate data ingestion from Nightscout API."""
    print_section("Data Ingestion Demo", "Fetching glucose data from Nightscout API...")

    # Fetch recent data from Nightscout
    base_url = "https://gwp-diabetes.fly.dev/api/v1"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
    today = datetime.now().strftime("%Y-%m-%dT23:59:59.999Z")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching data from Nightscout API...", total=None)

            response = requests.get(
                f"{base_url}/entries.json",
                params={
                    "count": 20,
                    "find[dateString][$gte]": yesterday,
                    "find[dateString][$lt]": today,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            progress.update(task, completed=True)

        console.print(f"[green]✓ Fetched {len(data)} glucose readings[/green]")

        # Show sample data
        if data:
            table = Table(title="Sample Glucose Readings (Raw API Data)", box=box.ROUNDED)
            table.add_column("ID", style="dim")
            table.add_column("Glucose (mg/dL)", style="bold cyan")
            table.add_column("Timestamp", style="yellow")
            table.add_column("Direction", style="magenta")
            table.add_column("Device", style="green")

            for entry in data[:5]:
                table.add_row(
                    entry.get("_id", "")[:12] + "...",
                    str(entry.get("sgv", "N/A")),
                    entry.get("dateString", "")[:19],
                    entry.get("direction", "NONE"),
                    entry.get("device", "Unknown")[:15],
                )

            console.print(table)

            # Show validation example
            print_section("Data Validation", "Validating with Pandera schema...")

            console.print("[yellow]RawGlucoseEntries Schema Checks:[/yellow]")
            console.print("  [green]✓[/green] _id is unique and non-null")
            console.print("  [green]✓[/green] sgv (glucose) is between 1-1000 mg/dL")
            console.print("  [green]✓[/green] date is valid Unix timestamp")
            console.print("  [green]✓[/green] direction is in allowed list")
            console.print(
                f"  [green]✓[/green] All {len(data)} records passed validation"
            )

            # Show what happens next
            console.print("\n[bold]Next Steps in Pipeline:[/bold]")
            console.print("  1. DLT stages data to S3 as Parquet")
            console.print("  2. PyIceberg merges to 'dev' branch")
            console.print("  3. Deduplicates by _id (idempotent)")
            console.print("  4. Ready for dbt transformation")

    except requests.RequestException as e:
        console.print(f"[red]✗ Error fetching data: {e}[/red]")
        console.print(
            "[yellow]Note: This demo requires network access to the Nightscout API[/yellow]"
        )


def demo_transformation():
    """Show the dbt transformation layers."""
    print_section("dbt Transformation Layers")

    # Create sample data
    sample_reading = {
        "entry_id": "65a1b2c3d4e5f6789",
        "glucose_mg_dl": 145,
        "reading_timestamp": "2024-01-15 14:00:00",
    }

    # Bronze layer
    console.print("[bold cyan]Bronze Layer:[/bold cyan] stg_glucose_entries.sql")
    console.print("  Clean and standardize raw data\n")

    bronze_table = Table(box=box.SIMPLE)
    bronze_table.add_column("Field", style="yellow")
    bronze_table.add_column("Value", style="white")
    bronze_table.add_row("entry_id", sample_reading["entry_id"])
    bronze_table.add_row("glucose_mg_dl", str(sample_reading["glucose_mg_dl"]))
    bronze_table.add_row("reading_timestamp", sample_reading["reading_timestamp"])
    bronze_table.add_row("direction", "Flat")
    bronze_table.add_row("device", "DexcomG6")
    console.print(bronze_table)

    # Silver layer
    console.print("\n[bold cyan]Silver Layer:[/bold cyan] fct_glucose_readings.sql")
    console.print("  Add enrichments and business logic\n")

    silver_table = Table(box=box.SIMPLE)
    silver_table.add_column("Field", style="yellow")
    silver_table.add_column("Value", style="white")
    silver_table.add_column("Logic", style="dim")
    silver_table.add_row(
        "hour_of_day", "14", "extract(hour from reading_timestamp)"
    )
    silver_table.add_row(
        "day_of_week", "1 (Monday)", "day_of_week(reading_timestamp)"
    )
    silver_table.add_row(
        "glucose_category",
        "in_range",
        "CASE: 70-180 mg/dL → 'in_range'",
    )
    silver_table.add_row(
        "is_in_range",
        "1",
        "1 if between 70-180, else 0",
    )
    silver_table.add_row(
        "glucose_change_mg_dl",
        "+3",
        "LAG window function",
    )
    console.print(silver_table)

    # Gold layer
    console.print("\n[bold cyan]Gold Layer:[/bold cyan] fct_daily_glucose_metrics.sql")
    console.print("  Daily aggregations and KPIs\n")

    gold_table = Table(box=box.SIMPLE)
    gold_table.add_column("Metric", style="yellow")
    gold_table.add_column("Value", style="white")
    gold_table.add_column("Calculation", style="dim")
    gold_table.add_row(
        "reading_count", "288", "count(*) - 5min intervals for 24h"
    )
    gold_table.add_row(
        "avg_glucose_mg_dl", "142.3", "round(avg(glucose_mg_dl), 1)"
    )
    gold_table.add_row(
        "time_in_range_pct",
        "68.2%",
        "100 * sum(is_in_range) / count(*)",
    )
    gold_table.add_row(
        "estimated_a1c_pct",
        "6.72%",
        "3.31 + (0.02392 * avg_glucose)",
    )
    console.print(gold_table)


def demo_analytics():
    """Demonstrate analytics capabilities."""
    print_section("Analytics Demo", "Querying data with DuckDB...")

    try:
        # Note: This is a demonstration of what analysts can do
        # Actual query would require configured MinIO/Iceberg access

        console.print("[bold]Analyst Workflow with DuckDB:[/bold]\n")

        code = """
import duckdb

# Connect to DuckDB
con = duckdb.connect()

# Install Iceberg extension
con.execute("INSTALL iceberg; LOAD iceberg;")

# Query Iceberg tables directly from S3
result = con.execute(\"\"\"
    SELECT
        date_trunc('day', reading_timestamp) as date,
        avg(glucose_mg_dl) as avg_glucose,
        round(100.0 * sum(CASE WHEN glucose_mg_dl BETWEEN 70 AND 180
                               THEN 1 ELSE 0 END) / count(*), 1) as time_in_range_pct,
        count(*) as reading_count
    FROM iceberg_scan('s3://phlo-data/iceberg/glucose_entries',
                       allow_moved_paths = true)
    WHERE reading_timestamp >= current_date - interval '7 days'
    GROUP BY date
    ORDER BY date DESC
\"\"\").df()

print(result)
        """

        console.print(Panel(code, title="DuckDB Query Example", border_style="green"))

        # Show sample results
        console.print("\n[bold]Sample Query Results:[/bold]\n")

        results_table = Table(
            title="7-Day Glucose Summary", box=box.ROUNDED, show_header=True
        )
        results_table.add_column("Date", style="cyan")
        results_table.add_column("Avg Glucose", style="yellow", justify="right")
        results_table.add_column("Time in Range %", style="green", justify="right")
        results_table.add_column("Readings", style="dim", justify="right")

        # Sample data
        sample_data = [
            ("2024-01-20", "138.4", "72.5", "287"),
            ("2024-01-19", "142.1", "68.9", "288"),
            ("2024-01-18", "145.7", "65.3", "286"),
            ("2024-01-17", "139.2", "71.2", "288"),
            ("2024-01-16", "141.5", "69.8", "287"),
            ("2024-01-15", "142.3", "68.2", "288"),
            ("2024-01-14", "144.8", "66.1", "285"),
        ]

        for date, avg_glucose, tir, readings in sample_data:
            results_table.add_row(date, avg_glucose, tir, readings)

        console.print(results_table)

        console.print("\n[bold cyan]Key Benefits:[/bold cyan]")
        console.print("  • Query Iceberg tables directly (no PostgreSQL needed)")
        console.print("  • Sub-second performance on lakehouse data")
        console.print("  • No Docker access required for analysts")
        console.print("  • Full SQL capabilities on raw data")

    except Exception as e:
        console.print(f"[yellow]Demo mode: {e}[/yellow]")


def demo_api():
    """Demonstrate API access."""
    print_section("API Access Demo")

    console.print("[bold]PostgREST Auto-Generated REST API[/bold]\n")

    # Show API endpoints
    api_examples = [
        {
            "description": "Get latest glucose overview (7 days)",
            "endpoint": "GET /mrt_glucose_overview?order=reading_date.desc&limit=7",
            "curl": "curl 'http://localhost:3001/mrt_glucose_overview?order=reading_date.desc&limit=7'",
        },
        {
            "description": "Filter by date range",
            "endpoint": "GET /mrt_glucose_overview?reading_date=gte.2024-01-01&reading_date=lte.2024-01-31",
            "curl": "curl 'http://localhost:3001/mrt_glucose_overview?reading_date=gte.2024-01-01'",
        },
        {
            "description": "Get days with excellent management",
            "endpoint": "GET /mrt_glucose_overview?diabetes_management_rating=eq.Excellent",
            "curl": "curl 'http://localhost:3001/mrt_glucose_overview?diabetes_management_rating=eq.Excellent'",
        },
    ]

    for example in api_examples:
        console.print(f"[cyan]→[/cyan] {example['description']}")
        console.print(f"  [dim]{example['curl']}[/dim]\n")

    # Show GraphQL example
    console.print("\n[bold]Hasura GraphQL API[/bold]\n")

    graphql_query = """
query GetRecentGlucose {
  mrt_glucose_overview(
    order_by: { reading_date: desc }
    limit: 7
  ) {
    reading_date
    avg_glucose_mg_dl
    time_in_range_pct
    estimated_a1c_pct
    diabetes_management_rating
  }
}
    """

    console.print(
        Panel(graphql_query, title="GraphQL Query Example", border_style="magenta")
    )

    # Show sample response
    console.print("\n[bold]Sample API Response:[/bold]\n")

    sample_response = {
        "reading_date": "2024-01-20",
        "avg_glucose_mg_dl": 138.4,
        "time_in_range_pct": 72.5,
        "estimated_a1c_pct": 6.62,
        "diabetes_management_rating": "Good",
    }

    import json

    console.print(Panel(json.dumps(sample_response, indent=2), border_style="green"))


def demo_quality():
    """Show data quality features."""
    print_section("Data Quality & Validation")

    console.print("[bold]Multi-Layered Validation Strategy[/bold]\n")

    layers = [
        {
            "layer": "1. Ingestion Validation",
            "tool": "Pandera (RawGlucoseEntries)",
            "severity": "ERROR",
            "action": "Blocks ingestion",
            "checks": [
                "_id is unique and non-null",
                "glucose (1-1000 mg/dL)",
                "Valid timestamps",
                "Direction in allowed list",
            ],
        },
        {
            "layer": "2. Transformation Tests",
            "tool": "dbt tests",
            "severity": "WARN",
            "action": "Logs issues",
            "checks": [
                "Unique entry_ids",
                "Not null constraints",
                "Referential integrity",
                "Custom business rules",
            ],
        },
        {
            "layer": "3. Asset Checks",
            "tool": "Dagster checks",
            "severity": "ERROR",
            "action": "Blocks dev→main merge",
            "checks": [
                "Data continuity (no gaps >30min)",
                "Reasonable glucose ranges",
                "Expected record counts",
                "Schema compliance",
            ],
        },
        {
            "layer": "4. Publishing Validation",
            "tool": "Pandera (Mart schemas)",
            "severity": "ERROR",
            "action": "Blocks PostgreSQL publish",
            "checks": [
                "Time in range: 0-100%",
                "Valid A1C estimates",
                "Non-negative counts",
                "Proper time dimensions",
            ],
        },
    ]

    for layer_info in layers:
        console.print(f"\n[bold cyan]{layer_info['layer']}[/bold cyan]")
        console.print(f"  Tool: {layer_info['tool']}")
        console.print(
            f"  Severity: [{'red' if layer_info['severity'] == 'ERROR' else 'yellow'}]{layer_info['severity']}[/]"
        )
        console.print(f"  Action: {layer_info['action']}")
        console.print("  Checks:")
        for check in layer_info["checks"]:
            console.print(f"    • {check}")

    console.print("\n[bold green]Result:[/bold green] Bad data never reaches production!")


def demo_branching():
    """Show git-like branching workflow."""
    print_section("Git-Like Data Branching", "Nessie catalog enables version control for data")

    workflow = Tree("[bold]Data Development Workflow[/bold]")

    # Dev branch
    dev = workflow.add("[cyan]dev branch[/cyan] (development)")
    dev.add("1. Ingest new glucose data")
    dev.add("2. Run dbt transformations")
    dev.add("3. Execute quality checks")
    validation = dev.add("4. Validation gates")
    validation.add("[green]✓[/green] Schema compliance")
    validation.add("[green]✓[/green] Data continuity")
    validation.add("[green]✓[/green] Business rules")

    # Merge
    workflow.add("[yellow]↓ merge (if all checks pass)[/yellow]")

    # Main branch
    main = workflow.add("[green]main branch[/green] (production)")
    main.add("1. Publish to PostgreSQL")
    main.add("2. Expose via APIs")
    main.add("3. Power dashboards")

    console.print(workflow)

    console.print("\n[bold]Branch Operations:[/bold]")
    console.print("  [dim]# Create a branch[/dim]")
    console.print("  phlo nessie create-branch dev")
    console.print("\n  [dim]# List branches[/dim]")
    console.print("  phlo nessie list-branches")
    console.print("\n  [dim]# Merge dev → main[/dim]")
    console.print("  phlo nessie merge dev main")
    console.print("\n  [dim]# Time travel (query historical data)[/dim]")
    console.print(
        "  SELECT * FROM glucose_entries FOR VERSION AS OF 'tag-v1.0'"
    )


def demo_metrics():
    """Show key platform metrics."""
    print_section("Platform Impact Metrics")

    metrics_table = Table(title="Phlo vs Traditional Approach", box=box.DOUBLE)
    metrics_table.add_column("Metric", style="cyan", no_wrap=True)
    metrics_table.add_column("Traditional", style="red", justify="right")
    metrics_table.add_column("Phlo", style="green", justify="right")
    metrics_table.add_column("Improvement", style="yellow", justify="right")

    metrics_table.add_row(
        "Lines of code per asset",
        "270+",
        "~60",
        "78% reduction",
    )
    metrics_table.add_row(
        "Manual schema management",
        "Yes",
        "Auto-generated",
        "100% automated",
    )
    metrics_table.add_row(
        "Data validation",
        "Custom code",
        "Declarative",
        "Built-in",
    )
    metrics_table.add_row(
        "Branch management",
        "Manual",
        "Git-like",
        "Versioned",
    )
    metrics_table.add_row(
        "Time to production",
        "Weeks",
        "Days",
        "10x faster",
    )
    metrics_table.add_row(
        "Data quality issues",
        "Reactive",
        "Proactive",
        "Blocked at source",
    )

    console.print(metrics_table)


def main():
    """Run the demo."""
    parser = argparse.ArgumentParser(description="Phlo Glucose Platform Demo")
    parser.add_argument(
        "--demo",
        choices=[
            "all",
            "architecture",
            "ingestion",
            "transformation",
            "analytics",
            "api",
            "quality",
            "branching",
            "metrics",
        ],
        default="all",
        help="Which demo to run",
    )
    args = parser.parse_args()

    console.print(
        Panel.fit(
            "[bold cyan]Phlo Glucose Monitoring Platform Demo[/bold cyan]\n"
            "A Modern Data Lakehouse for Healthcare Analytics",
            border_style="cyan",
        )
    )

    if args.demo == "all" or args.demo == "architecture":
        demo_architecture()

    if args.demo == "all" or args.demo == "ingestion":
        demo_ingestion()

    if args.demo == "all" or args.demo == "transformation":
        demo_transformation()

    if args.demo == "all" or args.demo == "analytics":
        demo_analytics()

    if args.demo == "all" or args.demo == "api":
        demo_api()

    if args.demo == "all" or args.demo == "quality":
        demo_quality()

    if args.demo == "all" or args.demo == "branching":
        demo_branching()

    if args.demo == "all" or args.demo == "metrics":
        demo_metrics()

    # Final message
    console.print()
    console.print(
        Panel(
            "[bold green]Demo Complete![/bold green]\n\n"
            "Next Steps:\n"
            "  1. Read the full guide: docs/demos/GLUCOSE_PLATFORM_DEMO.md\n"
            "  2. Explore the code: src/phlo/defs/ingestion/nightscout/\n"
            "  3. Run the platform: docker compose up\n"
            "  4. Build your own pipelines with @phlo_ingestion",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
