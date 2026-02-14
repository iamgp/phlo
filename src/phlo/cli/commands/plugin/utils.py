"""Shared utilities for plugin commands."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from packaging.version import parse
from rich.console import Console
from rich.table import Table

from phlo.plugins import get_plugin_info
from phlo.plugins.discovery import get_global_registry, get_service

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
    "catalogs": "catalogs",
}

PLUGIN_TYPE_CHOICES = [
    "sources",
    "quality",
    "transforms",
    "services",
    "hooks",
    "assets",
    "resources",
    "orchestrators",
    "catalogs",
]

INTERNAL_TO_REGISTRY_TYPE = {
    "source_connectors": "source",
    "quality_checks": "quality",
    "transformations": "transform",
    "services": "service",
    "hooks": "hooks",
    "asset_providers": "assets",
    "resource_providers": "resources",
    "orchestrators": "orchestrators",
    "catalogs": "catalogs",
}

SCAFFOLD_TYPE_MAP = {
    "sources": "source",
    "quality": "quality",
    "transforms": "transform",
    "services": "service",
    "hooks": "hook",
    "catalogs": "catalog",
    "assets": "asset",
    "resources": "resource",
    "orchestrators": "orchestrator",
}


def run_pip(args: list[str], *, timeout: float = 300) -> None:
    """Install packages using pip, with uv fallback for uv-managed environments."""
    if importlib.util.find_spec("pip") is not None:
        command = [sys.executable, "-m", "pip", *args]
    else:
        if shutil.which("uv") is None:
            raise RuntimeError(
                "pip module is unavailable and 'uv' is not installed; cannot install packages."
            )
        command = ["uv", "pip", *args]

    try:
        subprocess.run(command, check=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Install command timed out after {timeout}s: {' '.join(command)}"
        ) from exc


def registry_plugin_to_dict(plugin) -> dict:
    """Convert registry plugin to dictionary."""
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


def collect_installed_plugins(plugin_type: str) -> list[dict]:
    """Collect installed plugins of given type."""
    registry = get_global_registry()
    installed: list[dict] = []

    def add_plugin(plugin_key: str, name: str) -> None:
        info = get_plugin_info(plugin_key, name)
        if not info:
            return
        installed.append(
            {
                "name": info["name"],
                "type": INTERNAL_TO_REGISTRY_TYPE.get(plugin_key, plugin_key),
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


def collect_registry_plugins(plugin_type: str) -> list[dict]:
    """Collect registry plugins of given type."""
    from phlo.plugins.registry_client import list_registry_plugins

    registry_plugins = list_registry_plugins()
    if plugin_type != "all":
        # Translate CLI type to internal type first, then to registry type
        internal_type = PLUGIN_TYPE_MAP.get(plugin_type, plugin_type)
        registry_type = INTERNAL_TO_REGISTRY_TYPE.get(internal_type)
        registry_plugins = [plugin for plugin in registry_plugins if plugin.type == registry_type]
    return [registry_plugin_to_dict(plugin) for plugin in registry_plugins]


def render_plugin_table(title: str, plugins: list[dict]) -> None:
    """Render a table of plugins."""
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


def get_installed_version(package: str) -> str | None:
    """Get installed version of a package."""
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def version_tuple(version: str) -> tuple[int, object]:
    """Convert version string to tuple for comparison."""
    try:
        return (0, parse(version))
    except Exception:
        return (0, parse("0"))


def is_version_newer(installed: str, available: str) -> bool:
    """Check if available version is newer than installed."""
    try:
        return parse(available) > parse(installed)
    except Exception:
        return available != installed


def find_available_updates(registry_plugins) -> list[dict]:
    """Find available updates for installed plugins."""
    updates = []
    for plugin in registry_plugins:
        installed_version = get_installed_version(plugin.package)
        if not installed_version:
            continue
        if is_version_newer(installed_version, plugin.version):
            updates.append(
                {
                    "name": plugin.name,
                    "package": plugin.package,
                    "installed_version": installed_version,
                    "available_version": plugin.version,
                }
            )
    return updates


def create_plugin_package(plugin_name: str, plugin_type: str, plugin_path: Path):
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
        "catalog": "CatalogPlugin",
        "asset": "AssetProviderPlugin",
        "resource": "ResourceProviderPlugin",
        "orchestrator": "OrchestratorAdapterPlugin",
    }
    base_class = type_mapping.get(plugin_type)
    if base_class is None:
        raise ValueError(f"unknown plugin_type: {plugin_type}")

    entry_point_group = {
        "source": "phlo.plugins.sources",
        "quality": "phlo.plugins.quality",
        "transform": "phlo.plugins.transforms",
        "service": "phlo.plugins.services",
        "hook": "phlo.plugins.hooks",
        "catalog": "phlo.plugins.catalogs",
        "asset": "phlo.plugins.assets",
        "resource": "phlo.plugins.resources",
        "orchestrator": "phlo.plugins.orchestrators",
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

    if plugin_type in {"asset", "resource", "orchestrator"}:
        plugin_content += "\nfrom collections.abc import Iterable\n"
        spec_imports: list[str]
        if plugin_type == "resource":
            spec_imports = ["ResourceSpec"]
        elif plugin_type == "asset":
            spec_imports = ["AssetCheckSpec", "AssetSpec"]
        else:
            spec_imports = ["AssetCheckSpec", "AssetSpec", "ResourceSpec"]
        plugin_content += f"from phlo.capabilities.specs import {', '.join(spec_imports)}\n"

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
                filters=HookFilter(event_types={{"quality.result"}}),
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

    _PLUGIN_TYPE_TEMPLATES = {
        "source": '''
    def fetch_data(self, config: dict):
        """Fetch data from source."""
        # Implement your data fetching logic here
        raise NotImplementedError()

    def get_schema(self, config: dict) -> dict | None:
        """Get source schema."""
        # Return schema or None
        return None
''',
        "quality": '''
    def create_check(self, **kwargs):
        """Create quality check instance."""
        # Implement your quality check creation logic here
        raise NotImplementedError()
''',
        "transform": '''
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
''',
        "service": '''
    @property
    def service_definition(self) -> dict:
        """Return service definition."""
        return {
            "category": "custom",
            "compose": {
                "image": "your-service:latest",
            },
        }
''',
        "catalog": '''
    @property
    def targets(self) -> list[str]:
        """Return engine targets for this catalog."""
        return []

    @property
    def catalog_name(self) -> str:
        """Return catalog name."""
        return "example"

    def get_properties(self) -> dict[str, str]:
        """Return catalog properties."""
        return {"connector.name": "example"}
''',
        "asset": '''
    def get_assets(self) -> Iterable[AssetSpec]:
        """Return asset specs."""
        # Add asset definitions here
        return []

    def get_checks(self) -> Iterable[AssetCheckSpec]:
        """Return asset check specs."""
        # Add asset checks here
        return []
''',
        "resource": '''
    def get_resources(self) -> Iterable[ResourceSpec]:
        """Return resource specs."""
        # Add resource definitions here
        return []
''',
        "orchestrator": '''
    def build_definitions(
        self,
        *,
        assets: Iterable[AssetSpec],
        checks: Iterable[AssetCheckSpec],
        resources: Iterable[ResourceSpec],
    ):
        """Build orchestrator definitions from capability specs."""
        # Implement orchestrator-specific translation here
        raise NotImplementedError()
''',
    }

    plugin_content += _PLUGIN_TYPE_TEMPLATES.get(plugin_type, "")

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
    if hasattr(plugin, "initialize"):
        config = {{}}
        plugin.initialize(config)
        # Add more initialization tests


def test_plugin_cleanup(plugin):
    """Test plugin cleanup."""
    if hasattr(plugin, "cleanup"):
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
    accessor_map = {
        "hook": "get_hook_plugin",
        "source": "get_source_connector",
        "quality": "get_quality_check",
        "transform": "get_transformation",
        "service": "get_service",
    }
    accessor = accessor_map.get(plugin_type, "get_plugin")

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
```
"""
    if accessor == "get_plugin":
        internal_type = {
            "catalog": "catalogs",
            "asset": "asset_providers",
            "resource": "resource_providers",
            "orchestrator": "orchestrators",
        }.get(plugin_type, plugin_type)
        readme_content += f"""
```python
from phlo.plugins import get_plugin

plugin = get_plugin("{internal_type}", "{plugin_name}")
```
"""
    readme_content += """

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
