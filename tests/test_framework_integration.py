"""
Integration tests for workflow discovery system.

Tests the end-to-end workflow discovery and definitions building
for user projects using Phlo as an installable package.
"""

import tempfile
from pathlib import Path

import pytest
from dagster import Definitions

from phlo.framework.definitions import build_definitions
from phlo.framework.discovery import discover_user_workflows

pytestmark = pytest.mark.integration


def test_discover_empty_workflows_directory():
    """Test discovering workflows from empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_path = Path(tmpdir) / "workflows"
        workflows_path.mkdir()

        # Should return Definitions (may have dbt/publishing assets from config)
        defs = discover_user_workflows(workflows_path, clear_registries=True)

        assert isinstance(defs, Definitions)
        # Assets may include auto-discovered dbt/publishing assets from project config


def test_discover_workflows_with_simple_asset():
    """Test discovering a simple ingestion workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_path = Path(tmpdir) / "workflows"
        workflows_path.mkdir()

        # Create a simple workflow file
        ingestion_dir = workflows_path / "ingestion"
        ingestion_dir.mkdir()
        (ingestion_dir / "__init__.py").write_text("")

        # Create a simple ingestion workflow
        workflow_content = '''"""
Simple test workflow.
"""

from phlo_dlt import phlo_ingestion
from dlt.sources.rest_api import rest_api
from pandera.pandas import DataFrameModel


class TestSchema(DataFrameModel):
    id: str


@phlo_ingestion(
    table_name="test_data",
    unique_key="id",
    group="test",
    validation_schema=TestSchema,
)
def test_workflow(partition_date: str):
    """Test workflow for discovery."""
    source = rest_api({
        "client": {
            "base_url": "https://api.example.com",
        },
        "resources": [{
            "name": "test",
            "endpoint": {"path": "test"},
        }],
    })
    return source
'''
        (ingestion_dir / "test_workflow.py").write_text(workflow_content)

        # Discover workflows
        defs = discover_user_workflows(workflows_path, clear_registries=True)

        # Should find the asset
        assert isinstance(defs, Definitions)
        assets = list(defs.assets or [])
        assert len(assets) > 0

        # Check that the asset has the correct name
        asset_names = []
        for asset in assets:
            if hasattr(asset, "keys"):
                # Multi-asset definition
                asset_names.extend([str(key) for key in asset.keys])  # type: ignore[attr-defined]
            elif hasattr(asset, "key"):
                # Single asset definition
                asset_names.append(asset.key.to_string())  # type: ignore[attr-defined]

        assert any("dlt_test_data" in name for name in asset_names)


def test_build_definitions_with_user_workflows():
    """Test building complete definitions with user workflows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_path = Path(tmpdir) / "workflows"
        workflows_path.mkdir()

        # Create minimal workflow structure
        (workflows_path / "__init__.py").write_text("")

        # Build definitions (should work even with empty workflows)
        defs = build_definitions(workflows_path=workflows_path)

        assert isinstance(defs, Definitions)
        # Should at least have resources
        assert defs.resources is not None


def test_build_definitions_without_workflows_path():
    """Test that build_definitions handles missing workflows gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "nonexistent"

        # Should not raise, just log warning
        defs = build_definitions(workflows_path=non_existent)

        assert isinstance(defs, Definitions)


def test_cli_init_command_structure():
    """Test that phlo init creates correct project structure."""
    from phlo.cli.main import _create_project_structure

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test-project"

        _create_project_structure(project_dir, "test-project", "basic")

        # Check that all expected files/directories exist
        assert (project_dir / "workflows").is_dir()
        assert (project_dir / "workflows" / "__init__.py").exists()
        assert (project_dir / "workflows" / "ingestion").is_dir()
        assert (project_dir / "workflows" / "schemas").is_dir()
        assert (project_dir / "workflows" / "transforms" / "dbt").is_dir()
        assert (project_dir / "workflows" / "transforms" / "dbt" / "dbt_project.yml").exists()
        assert (project_dir / "tests").is_dir()
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / ".env.example").exists()
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "README.md").exists()

        # Check pyproject.toml content
        pyproject_content = (project_dir / "pyproject.toml").read_text()
        assert 'name = "test-project"' in pyproject_content
        assert '"phlo"' in pyproject_content


def test_cli_init_minimal_template():
    """Test that minimal template doesn't create dbt structure."""
    from phlo.cli.main import _create_project_structure

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "minimal-project"

        _create_project_structure(project_dir, "minimal-project", "minimal")

        # Should have workflows but not transforms
        assert (project_dir / "workflows").is_dir()
        assert not (project_dir / "workflows" / "transforms").exists()
