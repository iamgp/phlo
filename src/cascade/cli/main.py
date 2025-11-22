"""
Cascade CLI Main Entry Point

Provides command-line interface for Cascade workflows.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Optional, List
import click


@click.group()
@click.version_option(version="1.0.0", prog_name="cascade")
def cli():
    """
    Cascade - Modern Data Lakehouse Framework

    Build production-ready data pipelines with minimal boilerplate.

    Documentation: https://github.com/iamgp/cascade
    """
    pass


@cli.command()
@click.argument("asset_name", required=False)
@click.option("--local", is_flag=True, help="Run tests locally without Docker")
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-m", "--marker", help="Run tests with specific pytest marker")
def test(
    asset_name: Optional[str],
    local: bool,
    coverage: bool,
    verbose: bool,
    marker: Optional[str],
):
    """
    Run tests for Cascade workflows.

    Examples:
        cascade test                          # Run all tests
        cascade test weather_observations     # Run tests for specific asset
        cascade test --local                  # Run without Docker
        cascade test --coverage               # Generate coverage report
        cascade test -m integration           # Run integration tests only
    """
    click.echo("🧪 Running Cascade tests...\n")

    # Build pytest command
    pytest_args = ["pytest", "tests/"]

    if asset_name:
        # Run tests for specific asset
        test_file = f"tests/test_{asset_name}.py"
        if Path(test_file).exists():
            pytest_args = ["pytest", test_file]
        else:
            click.echo(f"❌ Test file not found: {test_file}", err=True)
            click.echo(f"\nAvailable test files:", err=True)
            for f in Path("tests").glob("test_*.py"):
                click.echo(f"  - {f.name}", err=True)
            sys.exit(1)

    if marker:
        pytest_args.extend(["-m", marker])
    elif local:
        # Skip integration tests that require Docker
        pytest_args.extend(["-m", "not integration"])

    if verbose:
        pytest_args.append("-v")

    if coverage:
        pytest_args.extend(["--cov=cascade", "--cov-report=html", "--cov-report=term"])

    # Run pytest
    try:
        result = subprocess.run(pytest_args, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("❌ pytest not found. Install with: pip install pytest", err=True)
        sys.exit(1)


@cli.command()
@click.argument("asset_name")
@click.option("-p", "--partition", help="Partition date (YYYY-MM-DD)")
@click.option("--select", help="Asset selector expression")
@click.option("--dry-run", is_flag=True, help="Show command without executing")
def materialize(
    asset_name: str,
    partition: Optional[str],
    select: Optional[str],
    dry_run: bool,
):
    """
    Materialize Dagster assets via Docker.

    Examples:
        cascade materialize weather_observations
        cascade materialize weather_observations --partition 2024-01-15
        cascade materialize --select "tag:weather"
        cascade materialize weather_observations --dry-run
    """
    # Build docker exec command
    cmd = [
        "docker", "exec", "dagster-webserver",
        "dagster", "asset", "materialize",
    ]

    if select:
        cmd.extend(["--select", select])
    else:
        cmd.extend(["--select", asset_name])

    if partition:
        cmd.extend(["--partition", partition])

    if dry_run:
        click.echo("🔍 Dry run - would execute:\n")
        click.echo(" ".join(cmd))
        sys.exit(0)

    click.echo(f"⚡ Materializing {asset_name}...\n")

    # Execute command
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            click.echo(f"\n✅ Successfully materialized {asset_name}")
        else:
            click.echo(f"\n❌ Materialization failed with exit code {result.returncode}", err=True)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("❌ Docker not found or dagster-webserver container not running", err=True)
        click.echo("\nStart services with: make up-core", err=True)
        sys.exit(1)


@cli.command("create-workflow")
@click.option("--type", "workflow_type", type=click.Choice(["ingestion", "transform", "quality"]), prompt="Workflow type", help="Type of workflow to create")
@click.option("--domain", prompt="Domain name", help="Domain name (e.g., weather, stripe, github)")
@click.option("--table", prompt="Table name", help="Table name for ingestion")
@click.option("--unique-key", prompt="Unique key field", help="Field name for deduplication (e.g., id, _id)")
@click.option("--cron", default="0 */1 * * *", prompt="Cron schedule", help="Cron schedule expression")
@click.option("--api-base-url", prompt="API base URL (optional)", default="", help="REST API base URL")
def create_workflow(
    workflow_type: str,
    domain: str,
    table: str,
    unique_key: str,
    cron: str,
    api_base_url: str,
):
    """
    Interactive workflow scaffolding.

    Creates all necessary files for a new workflow:
    - Pandera schema file
    - Ingestion asset file
    - Test file
    - Auto-registers domain

    Examples:
        cascade create-workflow                                # Interactive prompts
        cascade create-workflow --type ingestion --domain weather --table observations
    """
    from cascade.cli.scaffold import create_ingestion_workflow

    click.echo(f"\n🚀 Creating {workflow_type} workflow for {domain}.{table}...\n")

    try:
        if workflow_type == "ingestion":
            files = create_ingestion_workflow(
                domain=domain,
                table_name=table,
                unique_key=unique_key,
                cron=cron,
                api_base_url=api_base_url or None,
            )

            click.echo("✅ Created files:\n")
            for file_path in files:
                click.echo(f"  ✓ {file_path}")

            click.echo(f"\n📝 Next steps:")
            click.echo(f"  1. Edit schema: {files[0]}")
            click.echo(f"  2. Configure API: {files[1]}")
            click.echo(f"  3. Restart Dagster: docker restart dagster-webserver")
            click.echo(f"  4. Test: cascade test {domain}")
            click.echo(f"  5. Materialize: cascade materialize {table}")

        else:
            click.echo(f"❌ Workflow type '{workflow_type}' not yet implemented", err=True)
            click.echo("Currently supported: ingestion", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error creating workflow: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
