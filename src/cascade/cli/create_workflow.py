"""
Create Workflow Command

Scaffolds new Cascade workflows with interactive prompts.
"""

from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

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
    Scaffold a new Cascade workflow.

    Creates the necessary files and directory structure for a new workflow,
    including schema, asset definition, and tests.

    \b
    Examples:
      # Create weather ingestion workflow
      cascade create-workflow --type ingestion --domain weather

      # Create stripe ingestion with custom asset name
      cascade create-workflow --type ingestion --domain stripe --asset-name payments

      # Non-interactive mode
      cascade create-workflow --type ingestion --domain github --no-interactive
    """
    console.print("\n[bold blue]🚀 Cascade Workflow Scaffolder[/bold blue]\n")

    # Use asset_name or default to domain
    if not asset_name:
        asset_name = domain

    # Determine project root (look for src/cascade directory)
    project_root = _find_project_root()
    if not project_root:
        console.print(
            "[red]Error: Could not find Cascade project root.[/red]\n"
            + "Make sure you're in a Cascade project directory.",
            style="red",
        )
        raise click.Abort()

    console.print(f"[green]✓[/green] Found project root: {project_root}")

    # Collect configuration
    config = {
        "domain": domain,
        "asset_name": asset_name,
        "workflow_type": workflow_type,
        "project_root": project_root,
    }

    if interactive and workflow_type == "ingestion":
        config = _prompt_ingestion_config(config)

    # Display summary
    _display_config_summary(config)

    if interactive and not Confirm.ask(
        "\n[bold]Proceed with creation?[/bold]", default=True
    ):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Create files
    if workflow_type == "ingestion":
        _create_ingestion_workflow(config)
    elif workflow_type == "quality":
        console.print("[yellow]Quality workflow creation coming soon![/yellow]")
    elif workflow_type == "transformation":
        console.print("[yellow]Transformation workflow creation coming soon![/yellow]")

    # Final instructions
    _display_next_steps(config)


def _find_project_root() -> Path | None:
    """Find the Cascade project root directory."""
    current = Path.cwd()

    # Check current directory and parents
    for path in [current] + list(current.parents):
        if (path / "src" / "cascade").exists():
            return path

    return None


def _prompt_ingestion_config(config: dict[str, Any]) -> dict[str, Any]:
    """Prompt for ingestion workflow configuration."""
    console.print("\n[bold]Configuration:[/bold]\n")

    # Table name
    default_table = config["asset_name"]
    config["table_name"] = Prompt.ask(
        "Iceberg table name",
        default=default_table,
    )

    # Unique key
    config["unique_key"] = Prompt.ask(
        "Unique key field (for deduplication)",
        default="id",
    )

    # Cron schedule
    config["cron"] = Prompt.ask(
        "Cron schedule (leave empty for none)",
        default="0 */1 * * *",
    )

    # Freshness policy
    config["freshness_warn_hours"] = Prompt.ask(
        "Freshness warn threshold (hours)",
        default="1",
    )
    config["freshness_fail_hours"] = Prompt.ask(
        "Freshness fail threshold (hours)",
        default="24",
    )

    # API base URL (optional)
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
        console.print(f"  Table: [cyan]{config['table_name']}[/cyan]")
        console.print(f"  Unique Key: [cyan]{config['unique_key']}[/cyan]")
        console.print(f"  Schedule: [cyan]{config['cron']}[/cyan]")


def _create_ingestion_workflow(config: dict[str, Any]) -> None:
    """Create ingestion workflow files."""
    console.print("\n[bold]Creating files...[/bold]\n")

    project_root = config["project_root"]
    domain = config["domain"]
    asset_name = config["asset_name"]

    # Paths
    ingestion_dir = project_root / "src" / "cascade" / "defs" / "ingestion" / domain
    schema_file = project_root / "src" / "cascade" / "schemas" / f"{domain}.py"
    test_file = project_root / "tests" / f"test_{domain}_{asset_name}.py"
    init_file = project_root / "src" / "cascade" / "defs" / "ingestion" / "__init__.py"

    # Create ingestion directory
    ingestion_dir.mkdir(parents=True, exist_ok=True)
    console.print(
        f"[green]✓[/green] Created directory: {ingestion_dir.relative_to(project_root)}"
    )

    # Create asset file
    asset_file = ingestion_dir / f"{asset_name}.py"
    asset_content = _generate_asset_template(config)
    asset_file.write_text(asset_content)
    console.print(
        f"[green]✓[/green] Created asset: {asset_file.relative_to(project_root)}"
    )

    # Create __init__.py in domain directory
    domain_init = ingestion_dir / "__init__.py"
    if not domain_init.exists():
        domain_init.write_text(f'"""{domain.title()} domain ingestion assets."""\n')
        console.print(
            f"[green]✓[/green] Created: {domain_init.relative_to(project_root)}"
        )

    # Create schema file
    if not schema_file.exists():
        schema_content = _generate_schema_template(config)
        schema_file.write_text(schema_content)
        console.print(
            f"[green]✓[/green] Created schema: {schema_file.relative_to(project_root)}"
        )
    else:
        console.print(
            f"[yellow]ℹ[/yellow] Schema already exists: {schema_file.relative_to(project_root)}"
        )

    # Create test file
    if not test_file.parent.exists():
        test_file.parent.mkdir(parents=True, exist_ok=True)

    if not test_file.exists():
        test_content = _generate_test_template(config)
        test_file.write_text(test_content)
        console.print(
            f"[green]✓[/green] Created test: {test_file.relative_to(project_root)}"
        )
    else:
        console.print(
            f"[yellow]ℹ[/yellow] Test already exists: {test_file.relative_to(project_root)}"
        )

    # Update ingestion __init__.py to register domain
    _register_domain_import(init_file, domain, project_root)


def _register_domain_import(init_file: Path, domain: str, project_root: Path):
    """Add domain import to ingestion __init__.py."""
    import_line = f"from cascade.defs.ingestion import {domain}  # noqa: F401"

    if init_file.exists():
        content = init_file.read_text()
        if import_line in content:
            console.print(
                f"[yellow]ℹ[/yellow] Domain already registered in {init_file.relative_to(project_root)}"
            )
            return

        # Find insertion point (after other imports, before build_defs)
        lines = content.split("\n")
        insert_idx = 0

        for i, line in enumerate(lines):
            if line.startswith("from cascade.defs.ingestion import"):
                insert_idx = i + 1
            elif line.startswith("def build_defs"):
                break

        lines.insert(insert_idx, import_line)
        init_file.write_text("\n".join(lines))
        console.print(
            f"[green]✓[/green] Registered domain in: {init_file.relative_to(project_root)}"
        )
    else:
        console.print(
            f"[red]✗[/red] Could not find {init_file.relative_to(project_root)}"
        )


def _generate_asset_template(config: dict[str, Any]) -> str:
    """Generate asset Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    table_name = config["table_name"]
    unique_key = config["unique_key"]
    cron = config.get("cron", "0 */1 * * *")
    warn_hours = config.get("freshness_warn_hours", "1")
    fail_hours = config.get("freshness_fail_hours", "24")
    api_base_url = config.get("api_base_url", "https://api.example.com/v1")

    # Convert to proper types
    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
{domain.title()} {asset_name.title()} Ingestion

TODO: Update this docstring with your specific workflow description.
"""

from dlt.sources.rest_api import rest_api
from cascade.ingestion import cascade_ingestion
from cascade.schemas.{domain} import {schema_class}


@cascade_ingestion(
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

    TODO: Update this docstring with details about:
    - What data is being ingested
    - API endpoint being used
    - Any data transformations
    - Expected update frequency

    Args:
        partition_date: Date partition in YYYY-MM-DD format

    Returns:
        DLT source containing {asset_name} data
    """
    # TODO: Configure time range for your use case
    start_time = f"{{partition_date}}T00:00:00.000Z"
    end_time = f"{{partition_date}}T23:59:59.999Z"

    # TODO: Configure the DLT rest_api source for your API
    source = rest_api({{
        "client": {{
            "base_url": "{api_base_url}",

            # TODO: Configure authentication (uncomment one):

            # Option 1: Bearer token
            # "auth": {{
            #     "token": os.getenv("YOUR_API_TOKEN"),
            # }},

            # Option 2: API key in header
            # "headers": {{
            #     "X-API-Key": os.getenv("YOUR_API_KEY"),
            # }},
        }},

        "resources": [
            {{
                "name": "{asset_name}",
                "endpoint": {{
                    "path": "{asset_name}",  # TODO: Update with actual API path
                    "params": {{
                        "start_date": start_time,
                        "end_date": end_time,
                        # TODO: Add other required parameters
                    }},
                }},

                # TODO: Configure pagination if needed
                # "paginator": {{
                #     "type": "offset",
                #     "limit": 1000,
                # }},
            }},
        ],
    }})

    return source
'''


def _generate_schema_template(config: dict[str, Any]) -> str:
    """Generate schema Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    unique_key = config["unique_key"]

    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
{domain.title()} Data Schemas

Pandera schemas for {domain} domain data validation.
"""

import pandera as pa
from pandera.typing import Series


class {schema_class}(pa.DataFrameModel):
    """
    Schema for raw {asset_name} data.

    TODO: Update this schema with your actual data fields.
    """

    # TODO: Replace with your actual fields
    {unique_key}: Series[str] = pa.Field(
        nullable=False,
        description="Unique identifier for the record",
    )

    timestamp: Series[str] = pa.Field(
        nullable=False,
        description="ISO 8601 timestamp",
    )

    # TODO: Add more fields based on your API response
    # Example fields:
    # name: Series[str] = pa.Field(description="Name")
    # value: Series[float] = pa.Field(ge=0, le=1000, description="Value")
    # status: Series[str] = pa.Field(isin=["active", "inactive"], description="Status")

    class Config:
        """Pandera configuration."""
        strict = True  # Reject extra columns
        coerce = True  # Auto-convert types


# TODO: Add additional schemas if needed
'''


def _generate_test_template(config: dict[str, Any]) -> str:
    """Generate test Python code from template."""
    domain = config["domain"]
    asset_name = config["asset_name"]
    unique_key = config["unique_key"]

    schema_class = f"Raw{domain.title()}{asset_name.title()}"

    return f'''"""
Tests for {domain} {asset_name} workflow.
"""

import pytest
import pandas as pd
from cascade.schemas.{domain} import {schema_class}
from cascade.defs.ingestion.{domain}.{asset_name} import {asset_name}


class TestSchema:
    """Test schema validation."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""

        # TODO: Update with realistic test data
        test_data = pd.DataFrame([
            {{
                "{unique_key}": "test-001",
                "timestamp": "2024-01-15T12:00:00.000Z",
                # TODO: Add other required fields
            }},
        ])

        # Should not raise
        validated = {schema_class}.validate(test_data)
        assert len(validated) == 1

    def test_unique_key_exists_in_schema(self):
        """Test that unique_key field exists in schema."""

        schema_fields = {schema_class}.to_schema().columns.keys()
        assert "{unique_key}" in schema_fields


class TestAssetConfiguration:
    """Test asset decorator configuration."""

    def test_asset_has_correct_table_name(self):
        """Test that asset is configured with correct table name."""

        # Asset op name should be prefixed with 'dlt_'
        assert {asset_name}.op.name == "dlt_{config["table_name"]}"


# TODO: Add more tests
# - Test with invalid data (constraint violations)
# - Test business logic and transformations
# - Integration tests (require Docker)
'''


def _display_next_steps(config: dict[str, Any]) -> None:
    """Display next steps for user."""
    domain = config["domain"]
    asset_name = config["asset_name"]

    next_steps = f"""
[bold green]✓ Workflow created successfully![/bold green]

[bold]Next Steps:[/bold]

1. [cyan]Edit the schema[/cyan]: src/cascade/schemas/{domain}.py
   - Add your actual data fields
   - Set appropriate constraints

2. [cyan]Configure the asset[/cyan]: src/cascade/defs/ingestion/{domain}/{asset_name}.py
   - Update API endpoint and parameters
   - Configure authentication
   - Add pagination if needed

3. [cyan]Test your workflow[/cyan]:
   pytest tests/test_{domain}_{asset_name}.py -v

4. [cyan]Restart Dagster[/cyan]:
   docker restart dagster-webserver

5. [cyan]Materialize in UI[/cyan]:
   Open http://localhost:3000
   Navigate to Assets → {asset_name}
   Click "Materialize"

[bold]Documentation:[/bold]
- Full guide: docs/WORKFLOW_DEVELOPMENT_GUIDE.md
- Testing: docs/TESTING_GUIDE.md
- Troubleshooting: docs/TROUBLESHOOTING_GUIDE.md
"""

    console.print(Panel(next_steps, title="Success", border_style="green"))
