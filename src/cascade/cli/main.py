"""
Cascade CLI - Command Line Interface

Main entry point for the Cascade CLI tool.
"""

import click
from rich.console import Console

from cascade.cli.create_workflow import create_workflow
from cascade.cli.validate import validate_schema

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="cascade")
def cli():
    """
    Cascade - Lakehouse Platform CLI

    A command-line tool for managing Cascade workflows, testing, and validation.

    \b
    Common Commands:
      create-workflow    Scaffold a new ingestion workflow
      validate-schema    Validate a Pandera schema
      test              Test a workflow locally (coming soon)

    \b
    Examples:
      # Create a new REST API ingestion workflow
      cascade create-workflow --type ingestion --domain weather

      # Validate a schema file
      cascade validate-schema schemas/weather.py

      # Test an asset locally
      cascade test my_asset --partition 2024-01-15

    For more information, visit: https://docs.cascade.dev
    """
    pass


# Register commands
cli.add_command(create_workflow, name="create-workflow")
cli.add_command(validate_schema, name="validate-schema")


if __name__ == "__main__":
    cli()
