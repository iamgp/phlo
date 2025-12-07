"""Plugin Management Commands

CLI commands for managing Cascade plugins.

Provides commands to:
- List installed plugins
- Get detailed plugin information
- Validate plugin health
- Create scaffolding for new plugins
"""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from phlo.plugins import (
    discover_plugins,
    get_plugin_info,
    list_plugins,
    validate_plugins,
)

console = Console()


@click.group(name="plugin")
def plugin_group():
    """Manage Cascade plugins."""
    pass


@plugin_group.command(name="list")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["sources", "quality", "transforms", "all"]),
    default="all",
    help="Filter by plugin type",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def list_cmd(plugin_type: str, output_json: bool):
    """List all discovered plugins.

    Examples:
        phlo plugin list                    # List all plugins
        phlo plugin list --type sources     # List source connectors only
        phlo plugin list --json             # Output as JSON
    """
    try:
        all_plugins = list_plugins()

        if output_json:
            # Map display names to internal names
            type_mapping = {
                "sources": "source_connectors",
                "quality": "quality_checks",
                "transforms": "transformations",
            }

            output = {}
            for plugin_type_key, plugins in all_plugins.items():
                if plugin_type == "all" or type_mapping.get(plugin_type) == plugin_type_key:
                    output[plugin_type_key] = plugins

            console.print(json.dumps(output, indent=2))
            return

        # Rich table output
        if plugin_type == "all":
            # Show all plugin types
            type_groups = [
                ("Sources", all_plugins["source_connectors"]),
                ("Quality Checks", all_plugins["quality_checks"]),
                ("Transforms", all_plugins["transformations"]),
            ]
        else:
            type_mapping = {
                "sources": ("Sources", all_plugins["source_connectors"]),
                "quality": ("Quality Checks", all_plugins["quality_checks"]),
                "transforms": ("Transforms", all_plugins["transformations"]),
            }
            type_groups = [type_mapping[plugin_type]]

        for group_name, plugin_names in type_groups:
            if plugin_names:
                console.print(f"\n{group_name}:")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Name", style="cyan")
                table.add_column("Version", style="green")
                table.add_column("Author", style="yellow")

                for name in plugin_names:
                    # Get plugin info
                    type_key = None
                    if group_name == "Sources":
                        type_key = "source_connectors"
                    elif group_name == "Quality Checks":
                        type_key = "quality_checks"
                    elif group_name == "Transforms":
                        type_key = "transformations"

                    info = get_plugin_info(type_key, name)
                    if info:
                        table.add_row(
                            name,
                            info.get("version", "unknown"),
                            info.get("author", "unknown"),
                        )
                    else:
                        table.add_row(name, "unknown", "unknown")

                console.print(table)
            else:
                console.print(f"\n{group_name}:")
                console.print("  (none installed)")

    except Exception as e:
        console.print(f"[red]Error listing plugins: {e}[/red]")
        raise click.Exit(1)


@plugin_group.command(name="info")
@click.argument("plugin_name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["sources", "quality", "transforms"]),
    help="Plugin type (auto-detected if not specified)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def info_cmd(plugin_name: str, plugin_type: Optional[str], output_json: bool):
    """Show detailed plugin information.

    Examples:
        phlo plugin info github              # Show info for 'github' plugin
        phlo plugin info custom --type quality
        phlo plugin info github --json
    """
    try:
        all_plugins = list_plugins()

        # Auto-detect plugin type if not specified
        if not plugin_type:
            for ptype_key, names in all_plugins.items():
                if plugin_name in names:
                    if ptype_key == "source_connectors":
                        plugin_type = "sources"
                    elif ptype_key == "quality_checks":
                        plugin_type = "quality"
                    elif ptype_key == "transformations":
                        plugin_type = "transforms"
                    break

        if not plugin_type:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            raise click.Exit(1)

        # Map display names to internal names
        type_mapping = {
            "sources": "source_connectors",
            "quality": "quality_checks",
            "transforms": "transformations",
        }
        internal_type = type_mapping.get(plugin_type, plugin_type)

        info = get_plugin_info(internal_type, plugin_name)

        if not info:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            raise click.Exit(1)

        if output_json:
            console.print(json.dumps(info, indent=2))
            return

        # Rich formatted output
        console.print(f"\n[bold cyan]{info['name']}[/bold cyan]")
        console.print(f"Type: {plugin_type}")
        console.print(f"Version: {info['version']}")

        if info.get("author"):
            console.print(f"Author: {info['author']}")

        if info.get("description"):
            console.print(f"Description: {info['description']}")

        if info.get("license"):
            console.print(f"License: {info['license']}")

        if info.get("homepage"):
            console.print(f"Homepage: {info['homepage']}")

        if info.get("tags"):
            console.print(f"Tags: {', '.join(info['tags'])}")

        if info.get("dependencies"):
            console.print("Dependencies:")
            for dep in info["dependencies"]:
                console.print(f"  - {dep}")

    except click.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error getting plugin info: {e}[/red]")
        raise click.Exit(1)


@plugin_group.command(name="check")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def check_cmd(output_json: bool):
    """Validate installed plugins.

    Checks that all plugins comply with their interface requirements
    and reports any issues.

    Examples:
        phlo plugin check           # Check all plugins
        phlo plugin check --json    # Output as JSON
    """
    try:
        console.print("Validating plugins...")

        # First discover plugins
        discover_plugins(auto_register=True)

        # Then validate
        validation_results = validate_plugins()

        if output_json:
            console.print(json.dumps(validation_results, indent=2))
            return

        # Rich formatted output
        valid = validation_results.get("valid", [])
        invalid = validation_results.get("invalid", [])

        console.print(f"\n[green]✓ Valid Plugins: {len(valid)}[/green]")
        if valid:
            for plugin_id in valid:
                console.print(f"  [green]✓[/green] {plugin_id}")

        if invalid:
            console.print(f"\n[red]✗ Invalid Plugins: {len(invalid)}[/red]")
            for plugin_id in invalid:
                console.print(f"  [red]✗[/red] {plugin_id}")
            raise click.Exit(1)
        else:
            console.print("\n[green]All plugins are valid![/green]")

    except click.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error validating plugins: {e}[/red]")
        raise click.Exit(1)


@plugin_group.command(name="create")
@click.argument("plugin_name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["source", "quality", "transform"]),
    default="source",
    help="Type of plugin to create",
)
@click.option(
    "--path",
    type=click.Path(),
    help="Path for new plugin package (default: ./phlo-plugin-{name})",
)
def create_cmd(plugin_name: str, plugin_type: str, path: Optional[str]):
    """Create scaffolding for a new plugin.

    Examples:
        phlo plugin create my-source              # Create source connector plugin
        phlo plugin create my-check --type quality # Create quality check plugin
        phlo plugin create my-transform --type transform --path ./plugins/
    """
    try:
        # Validate plugin name
        if not plugin_name or not all(c.isalnum() or c in "-_" for c in plugin_name):
            console.print("[red]Invalid plugin name. Use alphanumeric characters, - and _[/red]")
            raise click.Exit(1)

        # Determine output path
        if not path:
            path = f"phlo-plugin-{plugin_name}"

        plugin_path = Path(path)
        if plugin_path.exists():
            console.print(f"[red]Path already exists: {path}[/red]")
            raise click.Exit(1)

        # Create plugin package structure
        _create_plugin_package(
            plugin_name=plugin_name,
            plugin_type=plugin_type,
            plugin_path=plugin_path,
        )

        console.print("\n[green]✓ Plugin created successfully![/green]")
        console.print("\nNext steps:")
        console.print(f"  1. cd {path}")
        console.print(f"  2. Edit the plugin in src/phlo_{plugin_name.replace('-', '_')}/")
        console.print("  3. Run tests: pytest tests/")
        console.print("  4. Install: pip install -e .")

    except click.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error creating plugin: {e}[/red]")
        raise click.Exit(1)


def _create_plugin_package(plugin_name: str, plugin_type: str, plugin_path: Path):
    """Create plugin package structure and files."""
    # Create directories
    src_dir = plugin_path / "src" / f"phlo_{plugin_name.replace('-', '_')}"
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = plugin_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    module_name = plugin_name.replace("-", "_")
    type_mapping = {
        "source": "SourceConnectorPlugin",
        "quality": "QualityCheckPlugin",
        "transform": "TransformationPlugin",
    }
    base_class = type_mapping[plugin_type]

    entry_point_group = {
        "source": "phlo.plugins.sources",
        "quality": "phlo.plugins.quality",
        "transform": "phlo.plugins.transforms",
    }[plugin_type]

    # Create __init__.py
    init_content = f'''"""
{plugin_name} plugin for Cascade

Plugin type: {plugin_type}
"""

from phlo_{module_name}.plugin import {plugin_name.replace("-", "_").title().replace("_", "")}Plugin

__all__ = ["{plugin_name.replace("-", "_").title().replace("_", "")}Plugin"]
__version__ = "0.1.0"
'''

    (src_dir / "__init__.py").write_text(init_content)

    # Create plugin.py
    class_name = plugin_name.replace("-", "_").title().replace("_", "") + "Plugin"
    plugin_content = f'''"""
{plugin_name} plugin implementation.
"""

from phlo.plugins import {base_class}, PluginMetadata


class {class_name}({base_class}):
    """
    {plugin_name} plugin.

    Add your implementation here.
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="{plugin_name}",
            version="0.1.0",
            description="Add description here",
            author="Your Name",
        )

    def initialize(self, config: dict) -> None:
        """Initialize plugin with configuration."""
        super().initialize(config)
        # Add initialization logic here

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        super().cleanup()
        # Add cleanup logic here
'''

    if plugin_type == "source":
        plugin_content += '''
    def fetch_data(self, config: dict):
        """Fetch data from source."""
        # Implement your data fetching logic here
        raise NotImplementedError()

    def get_schema(self, config: dict) -> dict | None:
        """Get source schema."""
        # Return schema or None
        return None
'''
    elif plugin_type == "quality":
        plugin_content += '''
    def create_check(self, **kwargs):
        """Create quality check instance."""
        # Implement your quality check creation logic here
        raise NotImplementedError()
'''
    elif plugin_type == "transform":
        plugin_content += '''
    def transform(self, df, config: dict):
        """Transform dataframe."""
        # Implement your transformation logic here
        raise NotImplementedError()

    def get_output_schema(self, input_schema: dict, config: dict) -> dict | None:
        """Get output schema."""
        # Return schema or None
        return None

    def validate_config(self, config: dict) -> bool:
        """Validate transformation configuration."""
        # Add config validation logic here
        return True
'''

    (src_dir / "plugin.py").write_text(plugin_content)

    # Create tests/__init__.py
    (tests_dir / "__init__.py").write_text("")

    # Create tests/test_plugin.py
    test_content = f'''"""
Tests for {plugin_name} plugin.
"""

import pytest
from phlo_{module_name}.plugin import {class_name}


@pytest.fixture
def plugin():
    """Create plugin instance."""
    return {class_name}()


def test_plugin_metadata(plugin):
    """Test plugin metadata."""
    metadata = plugin.metadata
    assert metadata.name == "{plugin_name}"
    assert metadata.version == "0.1.0"
    assert metadata.author is not None


def test_plugin_initialization(plugin):
    """Test plugin initialization."""
    config = {{}}
    plugin.initialize(config)
    # Add more initialization tests


def test_plugin_cleanup(plugin):
    """Test plugin cleanup."""
    plugin.cleanup()
    # Add more cleanup tests
'''

    (tests_dir / "test_plugin.py").write_text(test_content)

    # Create pyproject.toml
    pyproject_content = f'''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{plugin_name}"
version = "0.1.0"
description = "Cascade {plugin_type} plugin"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {{name = "Your Name", email = "your@email.com"}},
]
license = {{text = "MIT"}}
dependencies = [
    "cascade-sdk>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
    "basedpyright>=1.0.0",
]

[project.entry-points."{entry_point_group}"]
{plugin_name} = "phlo_{module_name}.plugin:{class_name}"

[tool.setuptools]
package-dir = {{"" = "src"}}

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.basedpyright]
typeCheckingMode = "standard"
'''

    (plugin_path / "pyproject.toml").write_text(pyproject_content)

    # Create README.md
    readme_content = f"""# {plugin_name}

A Cascade {plugin_type} plugin.

## Installation

```bash
pip install -e .
```

## Usage

```python
from phlo.plugins import get_{plugin_type.replace("transform", "transformation")}
from phlo_{module_name} import {class_name}

plugin = {class_name}()
# Use your plugin here
```

## Development

Run tests:
```bash
pytest tests/
```

Run linting:
```bash
ruff check .
basedpyright .
```

## License

MIT
"""

    (plugin_path / "README.md").write_text(readme_content)

    # Create MANIFEST.in
    (plugin_path / "MANIFEST.in").write_text("include README.md\nrecursive-include src *.py\n")
