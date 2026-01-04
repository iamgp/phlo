"""
Phlo CLI Main Entry Point

Provides command-line interface for Phlo workflows.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from phlo.cli.config import config
from phlo.cli.env import env
from phlo.cli.plugin import plugin_group
from phlo.cli.services import services
from phlo.logging import setup_logging


@click.group()
@click.version_option(version="1.0.0", prog_name="phlo")
def cli():
    """
    Phlo - Modern Data Lakehouse Framework

    Build production-ready data pipelines with minimal boilerplate.

    Documentation: https://github.com/iamgp/phlo
    """
    setup_logging()


cli.add_command(services)
cli.add_command(plugin_group)
cli.add_command(config)
cli.add_command(env)


def _load_cli_plugin_commands() -> None:
    from phlo.discovery import discover_plugins, get_global_registry

    discover_plugins(plugin_type="cli_commands", auto_register=True)
    registry = get_global_registry()
    for name in registry.list_cli_command_plugins():
        plugin = registry.get_cli_command_plugin(name)
        if plugin is None:
            continue
        for command in plugin.get_cli_commands():
            cli.add_command(command)


_load_cli_plugin_commands()


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
    Run tests for Phlo workflows.

    Examples:
        phlo test                          # Run all tests
        phlo test weather_observations     # Run tests for specific asset
        phlo test --local                  # Run without Docker
        phlo test --coverage               # Generate coverage report
        phlo test -m integration           # Run integration tests only
    """
    click.echo("Running Phlo tests...\n")

    # Build pytest command
    pytest_args = ["pytest"]

    if asset_name:
        # Run tests for specific asset
        test_file = f"tests/test_{asset_name}.py"
        if Path(test_file).exists():
            pytest_args = ["pytest", test_file]
        else:
            click.echo(f"Error: Test file not found: {test_file}", err=True)
            click.echo("\nAvailable test files:", err=True)
            for f in Path("tests").glob("test_*.py"):
                click.echo(f"  - {f.name}", err=True)
            sys.exit(1)

    if marker:
        pytest_args.extend(["-m", marker])
    elif local:
        # Skip integration tests that require Docker
        pytest_args.extend(["-m", "not integration"])

    # Set local test mode environment variable
    if local:
        os.environ["PHLO_TEST_LOCAL"] = "1"
        click.echo("Local test mode enabled (PHLO_TEST_LOCAL=1)\n")

    if verbose:
        pytest_args.append("-v")

    if coverage:
        pytest_args.extend(["--cov=phlo", "--cov-report=html", "--cov-report=term"])

    # Run pytest
    try:
        result = subprocess.run(pytest_args, check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo("Error: pytest not found. Install with: pip install pytest", err=True)
        sys.exit(1)


@cli.command("init")
@click.argument("project_name", required=False)
@click.option(
    "--template",
    type=click.Choice(["basic", "minimal"]),
    default="basic",
    help="Project template to use",
)
@click.option("--force", is_flag=True, help="Initialize in non-empty directory")
def init(project_name: Optional[str], template: str, force: bool):
    """
    Initialize a new Phlo project.

    Creates a minimal project structure for using Phlo as an installable package.
    Users only need to maintain workflow files, not the entire framework.

    Examples:
        phlo init my-data-project          # Create new project directory
        phlo init . --force                # Initialize in current directory
        phlo init weather-pipeline --template minimal
    """
    click.echo("Phlo Project Initializer\n")

    # Determine project directory
    if project_name is None or project_name == ".":
        project_dir = Path.cwd()
        project_name = project_dir.name
        click.echo(f"Initializing in current directory: {project_dir}")
    else:
        project_dir = Path.cwd() / project_name
        click.echo(f"Creating new project: {project_name}")

    # Check if directory exists and is not empty
    if project_dir.exists() and any(project_dir.iterdir()) and not force:
        click.echo(f"\nError: Directory {project_dir} is not empty", err=True)
        click.echo("Use --force to initialize anyway", err=True)
        sys.exit(1)

    # Create project structure
    try:
        _create_project_structure(project_dir, project_name, template)

        click.echo(f"\nSuccessfully initialized Phlo project: {project_name}\n")
        click.echo("Created structure:")
        click.echo(f"  {project_name}/")
        click.echo("  ├── phlo.yaml            # Project configuration with infrastructure")
        click.echo("  ├── pyproject.toml       # Project dependencies")
        click.echo("  ├── .env.example         # Local secrets template (copy to .phlo/.env.local)")
        click.echo("  ├── .sqlfluff            # SQL linting configuration for dbt models")
        click.echo("  ├── workflows/           # Your workflow definitions")
        click.echo("  │   ├── ingestion/       # Data ingestion workflows")
        click.echo("  │   ├── schemas/         # Pandera validation schemas")
        click.echo("  │   └── transforms/dbt/  # dbt transformation models")
        click.echo("  └── tests/               # Workflow tests")

        click.echo("\nNext steps:")
        if project_name != project_dir.name:
            click.echo(f"  1. cd {project_name}")
        click.echo("  2. pip install -e .              # Install Phlo and dependencies")
        click.echo("  3. phlo services init            # Set up infrastructure (Docker)")
        click.echo("  4. phlo create-workflow          # Create your first workflow")
        click.echo("  5. phlo dev                      # Start Dagster UI")

        click.echo("\nDocumentation: https://github.com/iamgp/phlo")

    except Exception as e:
        click.echo(f"\nError initializing project: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("dev")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=3000, type=int, help="Port to bind to")
@click.option("--workflows-path", default="workflows", help="Path to workflows directory")
def dev(host: str, port: int, workflows_path: str):
    """
    Start Dagster development server with your workflows.

    Automatically discovers workflows in ./workflows and launches the Dagster UI.

    Examples:
        phlo dev                              # Start on localhost:3000
        phlo dev --port 8080                  # Use custom port
        phlo dev --workflows-path custom_workflows
    """
    click.echo("Starting Phlo development server...\n")

    # Check if we're in a Phlo project
    if not Path("pyproject.toml").exists():
        click.echo("Error: No pyproject.toml found", err=True)
        click.echo("\nAre you in a Phlo project directory?", err=True)
        click.echo("Initialize a new project with: phlo init", err=True)
        sys.exit(1)

    # Check if workflows directory exists
    workflows_dir = Path(workflows_path)
    if not workflows_dir.exists():
        click.echo(f"Warning: Workflows directory not found: {workflows_path}")
        click.echo("Creating empty workflows directory...")
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "__init__.py").write_text('"""User workflows."""\n')

    # Set environment variable for workflows path
    os.environ["PHLO_WORKFLOWS_PATH"] = workflows_path

    click.echo(f"Workflows directory: {workflows_path}")
    click.echo(f"Starting server at http://{host}:{port}\n")

    # Build dagster dev command
    cmd = [
        "dagster",
        "dev",
        "-m",
        "phlo.framework.definitions",
        "-h",
        host,
        "-p",
        str(port),
    ]

    try:
        # Run dagster dev (blocking)
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\n\nShutting down Dagster development server...")
    except FileNotFoundError:
        click.echo("Error: dagster command not found", err=True)
        click.echo("\nInstall Phlo with: pip install -e .", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        click.echo(f"\nDagster failed with exit code {e.returncode}", err=True)
        sys.exit(e.returncode)


@cli.command("create-workflow")
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion", "transform", "quality"]),
    prompt="Workflow type",
    help="Type of workflow to create",
)
@click.option("--domain", prompt="Domain name", help="Domain name (e.g., weather, stripe, github)")
@click.option("--table", prompt="Table name", help="Table name for ingestion")
@click.option(
    "--unique-key",
    prompt="Unique key field",
    help="Field name for deduplication (e.g., id, _id)",
)
@click.option(
    "--cron",
    default="0 */1 * * *",
    prompt="Cron schedule",
    help="Cron schedule expression",
)
@click.option(
    "--api-base-url",
    prompt="API base URL (optional)",
    default="",
    help="REST API base URL",
)
@click.option(
    "--field",
    "fields",
    multiple=True,
    help="Additional schema field (name:type, name:type?, name:type!)",
)
def create_workflow(
    workflow_type: str,
    domain: str,
    table: str,
    unique_key: str,
    cron: str,
    api_base_url: str,
    fields: tuple[str, ...],
):
    """
    Interactive workflow scaffolding.

    Creates all necessary files for a new workflow:
    - Pandera schema file
    - Ingestion asset file
    - Test file
    - Auto-registers domain

    Examples:
        phlo create-workflow                                # Interactive prompts
        phlo create-workflow --type ingestion --domain weather --table observations
    """
    from phlo.cli.scaffold import create_ingestion_workflow

    click.echo(f"\nCreating {workflow_type} workflow for {domain}.{table}...\n")

    try:
        if workflow_type == "ingestion":
            files = create_ingestion_workflow(
                domain=domain,
                table_name=table,
                unique_key=unique_key,
                cron=cron,
                api_base_url=api_base_url or None,
                fields=list(fields),
            )

            click.echo("Created files:\n")
            for file_path in files:
                click.echo(f"  - {file_path}")

            click.echo("\nNext steps:")
            click.echo(f"  1. Edit schema: {files[0]}")
            click.echo(f"  2. Configure API: {files[1]}")
            click.echo("  3. Restart Dagster: docker restart dagster-webserver")
            click.echo(f"  4. Test: phlo test {domain}")
            click.echo(f"  5. Materialize: phlo materialize {table}")

        else:
            click.echo(f"Error: Workflow type '{workflow_type}' not yet implemented", err=True)
            click.echo("Currently supported: ingestion", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error creating workflow: {e}", err=True)
        sys.exit(1)


def _create_project_structure(project_dir: Path, project_name: str, template: str):
    """
    Create project directory structure and files.

    Args:
        project_dir: Path to project directory
        project_name: Name of the project
        template: Template type ("basic" or "minimal")
    """
    # Create directories
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create workflows structure
    workflows_dir = project_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    (workflows_dir / "__init__.py").write_text('"""User workflows."""\n')

    (workflows_dir / "ingestion").mkdir(exist_ok=True)
    (workflows_dir / "ingestion" / "__init__.py").write_text('"""Ingestion workflows."""\n')

    (workflows_dir / "schemas").mkdir(exist_ok=True)
    (workflows_dir / "schemas" / "__init__.py").write_text('"""Pandera validation schemas."""\n')

    # Create workflows/transforms/dbt structure if basic template
    if template == "basic":
        transforms_dir = project_dir / "workflows" / "transforms" / "dbt"
        transforms_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal dbt_project.yml
        dbt_project_content = f"""name: {project_name.replace("-", "_")}
version: 1.0.0
config-version: 2

profile: phlo

model-paths: ["models"]
seed-paths: ["seeds"]

# Opt into new SSL behavior to suppress trino-dbt SSL warning
flags:
  require_certificate_validation: true

models:
  {project_name.replace("-", "_")}:
    +materialized: table
"""
        (transforms_dir / "dbt_project.yml").write_text(dbt_project_content)

        # Create models directory
        (transforms_dir / "models").mkdir(exist_ok=True)
        (transforms_dir / "models" / ".gitkeep").write_text("")

    # Create tests directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "__init__.py").write_text("")

    # Create pyproject.toml
    pyproject_content = f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "Phlo data workflows"
requires-python = ">=3.11"
dependencies = [
    "phlo",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content)

    # Create .env.example (secrets template)
    env_example_content = """# Phlo Local Secrets Template
# Copy to .phlo/.env.local after running `phlo services init`.

# Postgres
POSTGRES_PASSWORD=phlo

# MinIO
MINIO_ROOT_PASSWORD=minio123
MINIO_OIDC_CLIENT_SECRET=
MINIO_LDAP_BIND_PASSWORD=

# Nessie
NESSIE_OIDC_CLIENT_SECRET=

# Trino
TRINO_OAUTH2_CLIENT_SECRET=
TRINO_HTTPS_KEYSTORE_PASSWORD=

# Superset
SUPERSET_SECRET_KEY=phlo-superset-secret-change-me
SUPERSET_ADMIN_PASSWORD=admin

# Hasura
HASURA_ADMIN_SECRET=phlo-hasura-admin-secret

# Grafana
GRAFANA_ADMIN_PASSWORD=admin
"""
    (project_dir / ".env.example").write_text(env_example_content)

    # Create .sqlfluff (for linting dbt SQL models)
    sqlfluff_content = """[sqlfluff]
dialect = trino
templater = jinja
max_line_length = 120
# Only exclude keywords-as-identifiers rule (requires column renames)
exclude_rules = RF04

[sqlfluff:templater:jinja]
# Ignore undefined jinja variables in dbt
ignore = templating

[sqlfluff:rules]
# Allow trailing commas
allow_trailing_commas = True

[sqlfluff:rules:layout.long_lines]
# Increase line length limit
max_line_length = 120

[sqlfluff:rules:layout.indent]
# Use 4 spaces for indentation
indent_unit = space
tab_space_size = 4

[sqlfluff:rules:capitalisation.keywords]
# SQL keywords should be lowercase
capitalisation_policy = lower

[sqlfluff:rules:aliasing.table]
# Table aliases are required
aliasing = explicit
"""
    (project_dir / ".sqlfluff").write_text(sqlfluff_content)

    # Create .gitignore
    gitignore_content = """.env
.env.local
.phlo/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/
"""
    (project_dir / ".gitignore").write_text(gitignore_content)

    # Create README.md
    readme_content = f"""# {project_name}

Phlo data workflows for {project_name}.

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Create your first workflow:**
   ```bash
   phlo create-workflow
   ```

3. **Start Dagster UI:**
   ```bash
   phlo dev
   ```

4. **Access the UI:**
   Open http://localhost:3000 in your browser

## Project Structure

```
{project_name}/
├── workflows/          # Your workflow definitions
│   ├── ingestion/     # Data ingestion workflows
│   ├── schemas/       # Pandera validation schemas
│   └── transforms/dbt/ # dbt transformation models
└── tests/            # Workflow tests
```

## Documentation

- [Phlo Documentation](https://github.com/iamgp/phlo)
- [Workflow Development Guide](https://github.com/iamgp/phlo/blob/main/docs/guides/workflow-development.md)

## Commands

- `phlo dev` - Start Dagster development server
- `phlo create-workflow` - Scaffold new workflow
- `phlo test` - Run tests
"""
    (project_dir / "README.md").write_text(readme_content)

    # Create phlo.yaml with infrastructure configuration
    from phlo.cli.services import PHLO_CONFIG_TEMPLATE

    phlo_config_content = PHLO_CONFIG_TEMPLATE.format(
        name=project_name,
        description=f"{project_name} data workflows",
    )
    (project_dir / "phlo.yaml").write_text(phlo_config_content)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
