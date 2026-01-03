"""Plugin Management Commands

CLI commands for managing Phlo plugins.

Provides commands to:
- List installed plugins
- Get detailed plugin information
- Validate plugin health
- Create scaffolding for new plugins
"""

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from phlo.discovery import get_global_registry, get_service
from phlo.plugins import (
    discover_plugins,
    get_plugin_info,
    list_plugins,
    validate_plugins,
)
from phlo.plugins.registry_client import (
    get_plugin as get_registry_plugin,
)
from phlo.plugins.registry_client import (
    list_registry_plugins,
    search_plugins,
)

console = Console()

PLUGIN_TYPE_MAP = {
    "sources": "source_connectors",
    "quality": "quality_checks",
    "transforms": "transformations",
    "services": "services",
    "hooks": "hooks",
    "assets": "asset_providers",
    "resources": "resource_providers",
    "orchestrators": "orchestrators",
}

PLUGIN_TYPE_LABELS = {
    "source_connectors": "Sources",
    "quality_checks": "Quality Checks",
    "transformations": "Transforms",
    "services": "Services",
    "hooks": "Hooks",
    "asset_providers": "Assets",
    "resource_providers": "Resources",
    "orchestrators": "Orchestrators",
}

PLUGIN_INTERNAL_TO_REGISTRY = {
    "source_connectors": "source",
    "quality_checks": "quality",
    "transformations": "transform",
    "services": "service",
    "hooks": "hooks",
    "asset_providers": "assets",
    "resource_providers": "resources",
    "orchestrators": "orchestrator",
}

REGISTRY_TYPE_MAP = {
    "sources": "source",
    "quality": "quality",
    "transforms": "transform",
    "services": "service",
    "hooks": "hooks",
    "assets": "assets",
    "resources": "resources",
    "orchestrators": "orchestrator",
}


@click.group(name="plugin")
def plugin_group():
    """Manage Phlo plugins."""
    pass


@plugin_group.command(name="list")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(
        [
            "sources",
            "quality",
            "transforms",
            "services",
            "hooks",
            "assets",
            "resources",
            "orchestrators",
            "all",
        ]
    ),
    default="all",
    help="Filter by plugin type",
)
@click.option(
    "--all",
    "include_registry",
    is_flag=True,
    default=False,
    help="Include registry plugins in output",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def list_cmd(plugin_type: str, include_registry: bool, output_json: bool):
    """List all discovered plugins.

    Examples:
        phlo plugin list                    # List all plugins
        phlo plugin list --type sources     # List source connectors only
        phlo plugin list --json             # Output as JSON
        phlo plugin list --all              # Include registry plugins
    """
    try:
        installed = _collect_installed_plugins(plugin_type)
        available = _collect_registry_plugins(plugin_type) if include_registry else []

        if output_json:
            output = {"installed": installed}
            if include_registry:
                output["available"] = available
            console.print(json.dumps(output if include_registry else installed, indent=2))
            return

        _render_plugin_table("Installed", installed)
        if include_registry:
            _render_plugin_table("Available", available)

    except Exception as e:
        console.print(f"[red]Error listing plugins: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="info")
@click.argument("plugin_name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(
        [
            "sources",
            "quality",
            "transforms",
            "services",
            "hooks",
            "assets",
            "resources",
            "orchestrators",
        ]
    ),
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
                    elif ptype_key == "services":
                        plugin_type = "services"
                    break

        if not plugin_type:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)

        # Map display names to internal names
        type_mapping = {
            "sources": "source_connectors",
            "quality": "quality_checks",
            "transforms": "transformations",
            "services": "services",
            "hooks": "hooks",
            "assets": "asset_providers",
            "resources": "resource_providers",
            "orchestrators": "orchestrators",
        }
        internal_type = type_mapping.get(plugin_type, plugin_type)

        info = get_plugin_info(internal_type, plugin_name)

        if not info:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            sys.exit(1)

        # Type narrowing for ty: info is guaranteed non-None here
        assert info is not None

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

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error getting plugin info: {e}[/red]")
        sys.exit(1)


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
            sys.exit(1)
        else:
            console.print("\n[green]All plugins are valid![/green]")

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error validating plugins: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="search")
@click.argument("query", required=False)
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["source", "quality", "transform", "service", "hooks"]),
    help="Filter by plugin type",
)
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Filter by one or more tags",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def search_cmd(
    query: Optional[str], plugin_type: Optional[str], tags: tuple[str, ...], output_json: bool
):
    """Search plugin registry."""
    try:
        results = search_plugins(
            query=query,
            plugin_type=plugin_type,
            tags=list(tags) if tags else None,
        )

        output = [_registry_plugin_to_dict(plugin) for plugin in results]

        if output_json:
            console.print(json.dumps(output, indent=2))
            return

        if not output:
            console.print("No plugins found.")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Package", style="white")
        table.add_column("Verified", style="blue")

        for plugin in output:
            table.add_row(
                plugin["name"],
                plugin["type"],
                plugin["version"],
                plugin["package"],
                "yes" if plugin["verified"] else "no",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error searching registry: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="install")
@click.argument("plugin_name")
def install_cmd(plugin_name: str):
    """Install a plugin from the registry (wraps pip)."""
    try:
        package_spec, display_name = _resolve_install_target(plugin_name)
        console.print(f"Installing {display_name}...")
        _run_pip(["install", package_spec])
        console.print(f"[green]✓ Installed {display_name}[/green]")
    except Exception as e:
        console.print(f"[red]Error installing plugin: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="update")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output as JSON",
)
def update_cmd(output_json: bool):
    """Update installed plugins based on registry versions."""
    try:
        registry_plugins = list_registry_plugins()
        updates = _find_available_updates(registry_plugins)

        if output_json:
            console.print(json.dumps(updates, indent=2))
            return

        if not updates:
            console.print("No plugin updates available.")
            return

        console.print("Updates available:")
        for update in updates:
            console.print(
                f"  {update['name']}: {update['installed_version']} → {update['available_version']}"
            )

        for update in updates:
            _run_pip(
                ["install", "--upgrade", f"{update['package']}=={update['available_version']}"]
            )

        console.print("[green]✓ Plugins updated[/green]")
    except Exception as e:
        console.print(f"[red]Error updating plugins: {e}[/red]")
        sys.exit(1)


@plugin_group.command(name="create")
@click.argument("plugin_name")
@click.option(
    "--type",
    "plugin_type",
    type=click.Choice(["source", "quality", "transform", "service", "hook"]),
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
            sys.exit(1)

        # Determine output path
        if not path:
            path = f"phlo-plugin-{plugin_name}"

        plugin_path = Path(path)
        if plugin_path.exists():
            console.print(f"[red]Path already exists: {path}[/red]")
            sys.exit(1)

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

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error creating plugin: {e}[/red]")
        sys.exit(1)


def _run_pip(args: list[str]) -> None:
    command = [sys.executable, "-m", "pip", *args]
    subprocess.run(command, check=True)


def _registry_plugin_to_dict(plugin) -> dict:
    return {
        "name": plugin.name,
        "type": plugin.type,
        "package": plugin.package,
        "version": plugin.version,
        "description": plugin.description,
        "author": plugin.author,
        "homepage": plugin.homepage,
        "tags": plugin.tags,
        "verified": plugin.verified,
        "core": plugin.core,
    }


def _resolve_install_target(plugin_name: str) -> tuple[str, str]:
    if "==" in plugin_name:
        name_part, version_part = plugin_name.split("==", 1)
    else:
        name_part, version_part = plugin_name, None

    registry_plugin = get_registry_plugin(name_part)
    if registry_plugin:
        version = version_part or registry_plugin.version
        package_spec = f"{registry_plugin.package}=={version}"
        display_name = f"{registry_plugin.name} ({registry_plugin.package})"
        return package_spec, display_name

    return plugin_name, plugin_name


def _collect_installed_plugins(plugin_type: str) -> list[dict]:
    registry = get_global_registry()
    installed: list[dict] = []

    def add_plugin(plugin_key: str, name: str) -> None:
        info = get_plugin_info(plugin_key, name)
        if not info:
            return
        installed.append(
            {
                "name": info["name"],
                "type": PLUGIN_INTERNAL_TO_REGISTRY.get(plugin_key, plugin_key),
                "version": info["version"],
                "description": info.get("description", ""),
                "author": info.get("author", ""),
                "homepage": info.get("homepage", ""),
                "tags": info.get("tags", []),
                "installed": True,
            }
        )

    for type_key, names in registry.list_all_plugins().items():
        if plugin_type != "all" and PLUGIN_TYPE_MAP.get(plugin_type) != type_key:
            continue
        if type_key == "services":
            for name in names:
                service = get_service(name)
                if not service:
                    continue
                metadata = service.metadata
                installed.append(
                    {
                        "name": metadata.name,
                        "type": "service",
                        "version": metadata.version,
                        "description": metadata.description,
                        "author": metadata.author,
                        "homepage": metadata.homepage,
                        "tags": metadata.tags,
                        "installed": True,
                        "category": service.category,
                        "profile": service.profile,
                        "default": service.is_default,
                    }
                )
            continue

        for name in names:
            add_plugin(type_key, name)

    return installed


def _collect_registry_plugins(plugin_type: str) -> list[dict]:
    registry_plugins = list_registry_plugins()
    if plugin_type != "all":
        registry_type = REGISTRY_TYPE_MAP.get(plugin_type)
        registry_plugins = [plugin for plugin in registry_plugins if plugin.type == registry_type]
    return [_registry_plugin_to_dict(plugin) for plugin in registry_plugins]


def _render_plugin_table(title: str, plugins: list[dict]) -> None:
    console.print(f"\n{title}:")
    if not plugins:
        console.print("  (none)")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Author", style="white")

    for plugin in plugins:
        table.add_row(
            plugin["name"],
            plugin["type"],
            plugin["version"],
            plugin.get("author", "unknown") or "unknown",
        )

    console.print(table)


def _get_installed_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _version_tuple(version: str) -> tuple:
    try:
        from packaging.version import Version

        return (0, Version(version))
    except Exception:
        parts = []
        for part in version.replace("-", ".").split("."):
            if part.isdigit():
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        return tuple(parts)


def _is_version_newer(installed: str, available: str) -> bool:
    try:
        return _version_tuple(available) > _version_tuple(installed)
    except Exception:
        return available != installed


def _find_available_updates(registry_plugins) -> list[dict]:
    updates = []
    for plugin in registry_plugins:
        installed_version = _get_installed_version(plugin.package)
        if not installed_version:
            continue
        if _is_version_newer(installed_version, plugin.version):
            updates.append(
                {
                    "name": plugin.name,
                    "package": plugin.package,
                    "installed_version": installed_version,
                    "available_version": plugin.version,
                }
            )
    return updates


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
        "service": "ServicePlugin",
        "hook": "HookPlugin",
    }
    base_class = type_mapping[plugin_type]

    entry_point_group = {
        "source": "phlo.plugins.sources",
        "quality": "phlo.plugins.quality",
        "transform": "phlo.plugins.transforms",
        "service": "phlo.plugins.services",
        "hook": "phlo.plugins.hooks",
    }[plugin_type]

    # Create __init__.py
    init_content = f'''"""
{plugin_name} plugin for Phlo

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
'''

    if plugin_type == "hook":
        plugin_content += f'''
from phlo.hooks import HookEvent
from phlo.plugins import HookFilter, HookRegistration


class {class_name}({base_class}):
    """
    {plugin_name} hook plugin.

    Add your hook handlers here.
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

    def get_hooks(self):
        """Return hook registrations."""
        return [
            HookRegistration(
                hook_name="handle_events",
                handler=self.handle_event,
                filters=HookFilter(event_types={"quality.result"}),
            )
        ]

    def handle_event(self, event: HookEvent) -> None:
        """Handle hook events."""
        # Add your hook logic here
        raise NotImplementedError()
'''
    else:
        plugin_content += f'''


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
    elif plugin_type == "service":
        plugin_content += '''
    @property
    def service_definition(self) -> dict:
        """Return service definition."""
        return {
            "category": "custom",
            "compose": {
                "image": "your-service:latest",
            },
        }
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
description = "Phlo {plugin_type} plugin"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {{name = "Your Name", email = "your@email.com"}},
]
license = {{text = "MIT"}}
dependencies = [
    "phlo>=0.1.0",
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
    accessor = (
        "get_hook_plugin"
        if plugin_type == "hook"
        else f"get_{plugin_type.replace('transform', 'transformation')}"
    )

    readme_content = f"""# {plugin_name}

A Phlo {plugin_type} plugin.

## Installation

```bash
pip install -e .
```

## Usage

```python
from phlo.plugins import {accessor}
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
