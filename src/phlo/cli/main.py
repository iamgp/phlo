"""
Cascade CLI Main Entry Point

Provides command-line interface for Cascade workflows.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Optional
import click


@click.group()
@click.version_option(version="1.0.0", prog_name="phlo")
def cli():
    """
    Cascade - Modern Data Lakehouse Framework

    Build production-ready data pipelines with minimal boilerplate.

    Documentation: https://github.com/iamgp/phlo
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
        phlo test                          # Run all tests
        phlo test weather_observations     # Run tests for specific asset
        phlo test --local                  # Run without Docker
        phlo test --coverage               # Generate coverage report
        phlo test -m integration           # Run integration tests only
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
            click.echo("\nAvailable test files:", err=True)
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
        pytest_args.extend(["--cov=phlo", "--cov-report=html", "--cov-report=term"])

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
        phlo materialize weather_observations
        phlo materialize weather_observations --partition 2024-01-15
        phlo materialize --select "tag:weather"
        phlo materialize weather_observations --dry-run
    """
    # Build docker exec command
    cmd = [
        "docker",
        "exec",
        "dagster-webserver",
        "dagster",
        "asset",
        "materialize",
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
            click.echo(
                f"\n❌ Materialization failed with exit code {result.returncode}",
                err=True,
            )
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo(
            "❌ Docker not found or dagster-webserver container not running", err=True
        )
        click.echo("\nStart services with: make up-core", err=True)
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
    Initialize a new Cascade project.

    Creates a minimal project structure for using Cascade as an installable package.
    Users only need to maintain workflow files, not the entire framework.

    Examples:
        phlo init my-data-project          # Create new project directory
        phlo init . --force                # Initialize in current directory
        phlo init weather-pipeline --template minimal
    """
    click.echo("🚀 Cascade Project Initializer\n")

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
        click.echo(f"\n❌ Directory {project_dir} is not empty", err=True)
        click.echo("Use --force to initialize anyway", err=True)
        sys.exit(1)

    # Create project structure
    try:
        _create_project_structure(project_dir, project_name, template)

        click.echo(f"\n✅ Successfully initialized Cascade project: {project_name}\n")
        click.echo("📁 Created structure:")
        click.echo(f"  {project_name}/")
        click.echo("  ├── pyproject.toml       # Project dependencies")
        click.echo("  ├── .env.example         # Environment variables template")
        click.echo("  ├── workflows/           # Your workflow definitions")
        click.echo("  │   ├── ingestion/       # Data ingestion workflows")
        click.echo("  │   └── schemas/         # Pandera validation schemas")
        click.echo("  ├── transforms/dbt/      # dbt transformation models")
        click.echo("  └── tests/               # Workflow tests")

        click.echo("\n📝 Next steps:")
        if project_name != project_dir.name:
            click.echo(f"  1. cd {project_name}")
        click.echo(
            "  2. pip install -e .              # Install Cascade and dependencies"
        )
        click.echo("  3. phlo create-workflow       # Create your first workflow")
        click.echo("  4. phlo dev                   # Start Dagster UI")

        click.echo("\n📚 Documentation: https://github.com/iamgp/phlo")

    except Exception as e:
        click.echo(f"\n❌ Error initializing project: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


@cli.command("dev")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=3000, type=int, help="Port to bind to")
@click.option(
    "--workflows-path", default="workflows", help="Path to workflows directory"
)
def dev(host: str, port: int, workflows_path: str):
    """
    Start Dagster development server with your workflows.

    Automatically discovers workflows in ./workflows and launches the Dagster UI.

    Examples:
        phlo dev                              # Start on localhost:3000
        phlo dev --port 8080                  # Use custom port
        phlo dev --workflows-path custom_workflows
    """
    click.echo("🚀 Starting Cascade development server...\n")

    # Check if we're in a Cascade project
    if not Path("pyproject.toml").exists():
        click.echo("❌ No pyproject.toml found", err=True)
        click.echo("\nAre you in a Cascade project directory?", err=True)
        click.echo("Initialize a new project with: phlo init", err=True)
        sys.exit(1)

    # Check if workflows directory exists
    workflows_dir = Path(workflows_path)
    if not workflows_dir.exists():
        click.echo(f"⚠️  Workflows directory not found: {workflows_path}")
        click.echo("Creating empty workflows directory...")
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "__init__.py").write_text('"""User workflows."""\n')

    # Set environment variable for workflows path
    os.environ["CASCADE_WORKFLOWS_PATH"] = workflows_path

    click.echo(f"📂 Workflows directory: {workflows_path}")
    click.echo(f"🌐 Starting server at http://{host}:{port}\n")

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
        click.echo("\n\n👋 Shutting down Dagster development server...")
    except FileNotFoundError:
        click.echo("❌ dagster command not found", err=True)
        click.echo("\nInstall Cascade with: pip install -e .", err=True)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        click.echo(f"\n❌ Dagster failed with exit code {e.returncode}", err=True)
        sys.exit(e.returncode)


@cli.command("create-workflow")
@click.option(
    "--type",
    "workflow_type",
    type=click.Choice(["ingestion", "transform", "quality"]),
    prompt="Workflow type",
    help="Type of workflow to create",
)
@click.option(
    "--domain", prompt="Domain name", help="Domain name (e.g., weather, stripe, github)"
)
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
        phlo create-workflow                                # Interactive prompts
        phlo create-workflow --type ingestion --domain weather --table observations
    """
    from phlo.cli.scaffold import create_ingestion_workflow

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

            click.echo("\n📝 Next steps:")
            click.echo(f"  1. Edit schema: {files[0]}")
            click.echo(f"  2. Configure API: {files[1]}")
            click.echo("  3. Restart Dagster: docker restart dagster-webserver")
            click.echo(f"  4. Test: phlo test {domain}")
            click.echo(f"  5. Materialize: phlo materialize {table}")

        else:
            click.echo(
                f"❌ Workflow type '{workflow_type}' not yet implemented", err=True
            )
            click.echo("Currently supported: ingestion", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error creating workflow: {e}", err=True)
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
    (workflows_dir / "ingestion" / "__init__.py").write_text(
        '"""Ingestion workflows."""\n'
    )

    (workflows_dir / "schemas").mkdir(exist_ok=True)
    (workflows_dir / "schemas" / "__init__.py").write_text(
        '"""Pandera validation schemas."""\n'
    )

    # Create transforms/dbt structure if basic template
    if template == "basic":
        transforms_dir = project_dir / "transforms" / "dbt"
        transforms_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal dbt_project.yml
        dbt_project_content = f"""name: {project_name.replace("-", "_")}
version: 1.0.0
config-version: 2

profile: phlo

model-paths: ["models"]
seed-paths: ["seeds"]

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

    # Create .env.example
    env_example_content = """# Cascade Configuration
CASCADE_WORKFLOWS_PATH=workflows

# Database Configuration
POSTGRES_PASSWORD=your_password_here
MINIO_ROOT_PASSWORD=your_password_here
SUPERSET_ADMIN_PASSWORD=your_password_here

# Optional: Override dbt location
# CASCADE_DBT_PROJECT_DIR_OVERRIDE=custom_dbt

# Optional: Include core examples
# CASCADE_INCLUDE_CORE_ASSETS=false
"""
    (project_dir / ".env.example").write_text(env_example_content)

    # Create .gitignore
    gitignore_content = """.env
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

Cascade data workflows for {project_name}.

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
│   └── schemas/       # Pandera validation schemas
├── transforms/dbt/    # dbt transformation models
└── tests/            # Workflow tests
```

## Documentation

- [Cascade Documentation](https://github.com/iamgp/phlo)
- [Workflow Development Guide](https://github.com/iamgp/phlo/blob/main/docs/guides/workflow-development.md)

## Commands

- `phlo dev` - Start Dagster development server
- `phlo create-workflow` - Scaffold new workflow
- `phlo test` - Run tests
"""
    (project_dir / "README.md").write_text(readme_content)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
