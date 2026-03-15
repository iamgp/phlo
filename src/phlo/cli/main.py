"""
Phlo CLI Main Entry Point

Provides command-line interface for Phlo workflows.
"""

import os
import subprocess
import sys
from pathlib import Path

import click

import phlo.cli._warning_filters  # noqa: F401
from phlo.cli.commands.authz import authz_group
from phlo.cli.commands.metrics import metrics_group
from phlo.cli.commands.migrate import migrate_group
from phlo.cli.commands.plugin import plugin_group
from phlo.cli.commands.schema_migrate import schema_migrate_group
from phlo.cli.commands.schema_registry_cli import contracts
from phlo.cli.commands.services import _register_commands as _register_service_commands
from phlo.cli.commands.services import services_group
from phlo.cli.commands.workflow import workflow_group
from phlo.cli.config import config
from phlo.cli.env import env
from phlo.logging import get_logger, setup_logging

logger = get_logger(__name__, service="phlo-cli")


@click.group()
@click.version_option(version="1.0.0", prog_name="phlo")
def cli() -> None:
    """
    Phlo - Modern Data Lakehouse Framework

    Build production-ready data pipelines with minimal boilerplate.

    Documentation: https://github.com/iamgp/phlo
    """
    setup_logging()


cli.add_command(services_group)
cli.add_command(workflow_group)
cli.add_command(plugin_group)
cli.add_command(schema_migrate_group)
cli.add_command(migrate_group)
cli.add_command(metrics_group)
cli.add_command(contracts)
cli.add_command(config)
cli.add_command(env)
cli.add_command(authz_group)

_register_service_commands()


def _load_cli_plugin_commands() -> None:
    from phlo.plugins.discovery import discover_plugins, get_global_registry

    logger.debug("cli_plugin_discovery_started")
    discover_plugins(plugin_type="cli_commands", auto_register=True, failure_level="debug")
    registry = get_global_registry()
    added_count = 0
    for name in registry.list_cli_command_plugins():
        plugin = registry.get_cli_command_plugin(name)
        if plugin is None:
            logger.warning("cli_plugin_missing_in_registry", plugin_name=name)
            continue
        for command in plugin.get_cli_commands():
            if command.name is None or command.name in cli.commands:
                logger.debug("cli_command_skipped", plugin_name=name, command_name=command.name)
                continue
            cli.add_command(command)
            added_count += 1
            logger.debug("cli_command_added", plugin_name=name, command_name=command.name)
    logger.debug("cli_plugin_discovery_completed", command_count=added_count)


_load_cli_plugin_commands()


@cli.command()
@click.argument("asset_name", required=False)
@click.option("--local", is_flag=True, help="Run tests locally without Docker")
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-m", "--marker", help="Run tests with specific pytest marker")
def test(
    asset_name: str | None,
    local: bool,
    coverage: bool,
    verbose: bool,
    marker: str | None,
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
            logger.warning("test_file_not_found", test_file=test_file)
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
        logger.error("pytest_binary_not_found")
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
def init(project_name: str | None, template: str, force: bool):
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

    # Determine project directory and metadata-safe project name
    if project_name is None or project_name == ".":
        project_dir = Path.cwd()
        project_metadata_name = project_dir.name
        click.echo(f"Initializing in current directory: {project_dir}")
    else:
        requested_path = Path(project_name).expanduser()
        project_dir = (
            requested_path if requested_path.is_absolute() else (Path.cwd() / requested_path)
        )
        project_metadata_name = project_dir.name
        click.echo(f"Creating new project: {project_dir}")

    # Check if directory exists and is not empty
    if project_dir.exists() and any(project_dir.iterdir()) and not force:
        click.echo(f"\nError: Directory {project_dir} is not empty", err=True)
        click.echo("Use --force to initialize anyway", err=True)
        sys.exit(1)

    # Create project structure
    try:
        _create_project_structure(project_dir, project_metadata_name, template)

        click.echo(f"\nSuccessfully initialized Phlo project: {project_dir}\n")
        click.echo("Created structure:")
        click.echo(f"  {project_dir}/")
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
        if project_dir != Path.cwd():
            click.echo(f"  1. cd {project_dir}")
        click.echo("  2. pip install -e .              # Install Phlo and dependencies")
        click.echo("  3. phlo services init            # Set up infrastructure (Docker)")
        click.echo("  4. phlo workflow create          # Create your first workflow")
        click.echo("  5. phlo dev                      # Start Dagster UI")

        click.echo("\nDocumentation: https://github.com/iamgp/phlo")

    except Exception as e:
        logger.exception("project_initialization_failed", project_dir=str(project_dir))
        click.echo(f"\nError initializing project: {e}", err=True)
        import traceback

        traceback.print_exc()
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
        try:
            from phlo_dbt.scaffold import write_dbt_scaffold
        except ImportError as exc:
            raise RuntimeError(
                "phlo-dbt is required for the basic template. "
                "Install phlo-dbt or use --template minimal."
            ) from exc

        write_dbt_scaffold(project_name, transforms_dir, project_dir)

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
    env_example_content = _build_env_example_content()
    (project_dir / ".env.example").write_text(env_example_content)

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
   phlo workflow create
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
- `phlo workflow create` - Scaffold new workflow
- `phlo test` - Run tests
"""
    (project_dir / "README.md").write_text(readme_content)

    # Create phlo.yaml with infrastructure configuration
    from phlo.cli.commands.services.utils import PHLO_CONFIG_TEMPLATE

    phlo_config_content = PHLO_CONFIG_TEMPLATE.format(
        name=project_name,
        description=f"{project_name} data workflows",
    )
    (project_dir / "phlo.yaml").write_text(phlo_config_content)


def _build_env_example_content() -> str:
    from phlo.plugins.discovery import ServiceDiscovery

    lines = [
        "# Phlo Local Secrets Template",
        "# Copy to .phlo/.env.local after running `phlo services init`.",
        "",
    ]

    discovery = ServiceDiscovery()
    services = discovery.discover()
    if not services:
        lines.append(
            "# No service plugins discovered; install service packages to populate secrets."
        )
        return "\n".join(lines) + "\n"

    for service in sorted(services.values(), key=lambda s: s.name):
        secrets = {key: cfg for key, cfg in service.env_vars.items() if cfg.get("secret") is True}
        if not secrets:
            continue
        lines.append(f"# {service.name}")
        for key in sorted(secrets.keys()):
            desc = secrets[key].get("description")
            if desc:
                lines.append(f"# {desc}")
            lines.append(f"{key}=")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
