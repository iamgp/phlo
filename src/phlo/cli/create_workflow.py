"""
Create Workflow Command

Scaffolds new phlo workflows with interactive prompts.
"""

from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


@click.command()
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion", "quality", "transformation"], case_sensitive=False),
    required=True,
    help="Type of workflow to create",
)
@click.option(
    "--domain",
    required=True,
    help="Domain name (e.g., weather, stripe, github)",
)
@click.option(
    "--asset-name",
    help="Asset name (defaults to domain name)",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Enable interactive prompts",
)
def create_workflow(
    workflow_type: str,
    domain: str,
    asset_name: str | None,
    interactive: bool,
):
    """
    Scaffold a new phlo workflow.

    Creates the necessary files and directory structure for a new workflow,
    including schema, asset definition, and tests.

    Examples:
      phlo create-workflow --type ingestion --domain weather
      phlo create-workflow --type ingestion --domain stripe --asset-name payments
      phlo create-workflow --type ingestion --domain github --no-interactive
    """
    console.print("\n[bold blue]Phlo Workflow Scaffolder[/bold blue]\n")

    if not asset_name:
        asset_name = domain

    project_root = _find_project_root()
    if not project_root:
        console.print(
            "[red]Error: Could not find project root.[/red]\n"
            + "Make sure you're in a phlo project directory with a workflows/ folder.",
            style="red",
        )
        raise click.Abort()

    console.print(f"[green]✓[/green] Found project root: {project_root}")

    config = {
        "domain": domain,
        "asset_name": asset_name,
        "workflow_type": workflow_type,
        "project_root": project_root,
    }

    if interactive and workflow_type == "ingestion":
        config = _prompt_ingestion_config(config)

    _display_config_summary(config)

    if interactive and not Confirm.ask("\n[bold]Proceed with creation?[/bold]", default=True):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    if workflow_type == "ingestion":
        _create_ingestion_workflow(config)
    elif workflow_type == "quality":
        console.print("[yellow]Quality workflow creation coming soon![/yellow]")
    elif workflow_type == "transformation":
        console.print("[yellow]Transformation workflow creation coming soon![/yellow]")

    _display_next_steps(config)


def _find_project_root() -> Path | None:
    """Find the project root directory."""
    current = Path.cwd()

    for path in [current] + list(current.parents):
        if (path / "workflows").exists():
            return path

    return None


def _prompt_ingestion_config(config: dict[str, Any]) -> dict[str, Any]:
    """Prompt for ingestion workflow configuration."""
    console.print("\n[bold]Configuration:[/bold]\n")

    config["table_name"] = Prompt.ask(
        "Iceberg table name",
        default=config["asset_name"],
    )

    config["unique_key"] = Prompt.ask(
        "Unique key field (for deduplication)",
        default="id",
    )

    config["cron"] = Prompt.ask(
        "Cron schedule (leave empty for none)",
        default="0 */1 * * *",
    )

    config["freshness_warn_hours"] = Prompt.ask(
        "Freshness warn threshold (hours)",
        default="1",
    )
    config["freshness_fail_hours"] = Prompt.ask(
        "Freshness fail threshold (hours)",
        default="24",
    )

    config["api_base_url"] = Prompt.ask(
        "API base URL (optional, can edit later)",
        default="https://api.example.com/v1",
    )

    return config


def _display_config_summary(config: dict[str, Any]) -> None:
    """Display configuration summary."""
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Domain: [cyan]{config['domain']}[/cyan]")
    console.print(f"  Asset: [cyan]{config['asset_name']}[/cyan]")
    console.print(f"  Type: [cyan]{config['workflow_type']}[/cyan]")

    if config["workflow_type"] == "ingestion":
        console.print(f"  Table: [cyan]{config.get('table_name', config['asset_name'])}[/cyan]")
        console.print(f"  Unique Key: [cyan]{config.get('unique_key', 'id')}[/cyan]")
        console.print(f"  Schedule: [cyan]{config.get('cron', 'none')}[/cyan]")


def _create_ingestion_workflow(config: dict[str, Any]) -> None:
    """Create ingestion workflow files."""
    console.print("\n[bold]Creating files...[/bold]\n")

    project_root = config["project_root"]
    domain = config["domain"]
    asset_name = config["asset_name"]

    # Paths - use workflows/ directory
    ingestion_dir = project_root / "workflows" / "ingestion" / domain
    schema_file = project_root / "workflows" / "schemas" / f"{domain}.py"
    test_file = project_root / "tests" / f"test_{domain}_{asset_name}.py"

    # Create directories
    ingestion_dir.mkdir(parents=True, exist_ok=True)
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created directory: {ingestion_dir.relative_to(project_root)}")

    # Create asset file
    asset_file = ingestion_dir / f"{asset_name}.py"
    asset_content = _generate_asset_template(config)
    asset_file.write_text(asset_content)
    console.print(f"[green]✓[/green] Created asset: {asset_file.relative_to(project_root)}")

    # Create __init__.py in domain directory
    domain_init = ingestion_dir / "__init__.py"
    if not domain_init.exists():
        domain_init.write_text(f'"""{domain.title()} domain ingestion assets."""\n')
        console.print(f"[green]✓[/green] Created: {domain_init.relative_to(project_root)}")

    # Create schema file
    if not schema_file.exists():
        schema_content = _generate_schema_template(config)
        schema_file.write_text(schema_content)
        console.print(f"[green]✓[/green] Created schema: {schema_file.relative_to(project_root)}")
    else:
        console.print(
            f"[yellow]![/yellow] Schema already exists: {schema_file.relative_to(project_root)}"
        )

    # Create test file
    if not test_file.parent.exists():
        test_file.parent.mkdir(parents=True, exist_ok=True)

    if not test_file.exists():
        test_content = _generate_test_template(config)
        test_file.write_text(test_content)
        console.print(f"[green]✓[/green] Created test: {test_file.relative_to(project_root)}")
    else:
        console.print(
            f"[yellow]![/yellow] Test already exists: {test_file.relative_to(project_root)}"
        )


def _generate_asset_template(config: dict[str, Any]) -> str:
    """Generate asset Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    table_name = config.get("table_name", asset_name)
    unique_key = config.get("unique_key", "id")
    cron = config.get("cron", "0 */1 * * *")
    warn_hours = config.get("freshness_warn_hours", "1")
    fail_hours = config.get("freshness_fail_hours", "24")
    api_base_url = config.get("api_base_url", "https://api.example.com/v1")

    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
{domain.title()} {asset_name.title()} Ingestion
"""

from dlt.sources.rest_api import rest_api
import phlo
from workflows.schemas.{domain} import {schema_class}


@phlo.ingestion(
    table_name="{table_name}",
    unique_key="{unique_key}",
    validation_schema={schema_class},
    group="{domain}",
    cron="{cron}",
    freshness_hours=({warn_hours}, {fail_hours}),
)
def {asset_name}(partition_date: str):
    """
    Ingest {asset_name} data from API.

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT source containing {asset_name} data
    """
    start_time = f"{{partition_date}}T00:00:00.000Z"
    end_time = f"{{partition_date}}T23:59:59.999Z"

    source = rest_api({{
        "client": {{
            "base_url": "{api_base_url}",
            # Configure authentication:
            # "auth": {{"token": os.getenv("YOUR_API_TOKEN")}},
        }},
        "resources": [
            {{
                "name": "{asset_name}",
                "endpoint": {{
                    "path": "{asset_name}",
                    "params": {{
                        "start_date": start_time,
                        "end_date": end_time,
                    }},
                }},
            }},
        ],
    }})

    return source
'''


def _generate_schema_template(config: dict[str, Any]) -> str:
    """Generate schema Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    unique_key = config.get("unique_key", "id")

    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
{domain.title()} Data Schemas
"""

import pandera as pa
from pandera.typing import Series


class {schema_class}(pa.DataFrameModel):
    """Schema for raw {asset_name} data."""

    {unique_key}: Series[str] = pa.Field(
        nullable=False,
        description="Unique identifier for the record",
    )

    timestamp: Series[str] = pa.Field(
        nullable=False,
        description="ISO 8601 timestamp",
    )

    class Config:
        strict = True
        coerce = True
'''


def _generate_test_template(config: dict[str, Any]) -> str:
    """Generate test Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    unique_key = config.get("unique_key", "id")

    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
Tests for {domain} {asset_name} workflow.
"""

import pytest
import pandas as pd
from workflows.schemas.{domain} import {schema_class}


class TestSchema:
    """Test schema validation."""

    def test_valid_data_passes_validation(self):
        test_data = pd.DataFrame([
            {{
                "{unique_key}": "test-001",
                "timestamp": "2024-01-15T12:00:00.000Z",
            }},
        ])

        validated = {schema_class}.validate(test_data)
        assert len(validated) == 1

    def test_unique_key_exists_in_schema(self):
        schema_fields = {schema_class}.to_schema().columns.keys()
        assert "{unique_key}" in schema_fields
'''


def _display_next_steps(config: dict[str, Any]) -> None:
    """Display next steps for user."""
    domain = config["domain"]
    asset_name = config["asset_name"]

    next_steps = f"""
[bold green]✓ Workflow created successfully![/bold green]

[bold]Next Steps:[/bold]

1. [cyan]Edit the schema[/cyan]: workflows/schemas/{domain}.py
   - Add your actual data fields

2. [cyan]Configure the asset[/cyan]: workflows/ingestion/{domain}/{asset_name}.py
   - Update API endpoint and authentication

3. [cyan]Test your workflow[/cyan]:
   pytest tests/test_{domain}_{asset_name}.py -v

4. [cyan]Start services[/cyan]:
   phlo services start

5. [cyan]Materialize in UI[/cyan]:
   Open Dagster UI and materialize the asset
"""

    console.print(Panel(next_steps, title="Success", border_style="green"))
