"""
Integration tests for workflow discovery system.

Tests the end-to-end workflow discovery and definitions building
for user projects using Cascade as an installable package.
"""

import tempfile
from pathlib import Path

from dagster import Definitions

from phlo.framework.discovery import discover_user_workflows
from phlo.framework.definitions import build_definitions


def test_discover_empty_workflows_directory():
    """Test discovering workflows from empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_path = Path(tmpdir) / "workflows"
        workflows_path.mkdir()

        # Should return empty Definitions
        defs = discover_user_workflows(workflows_path)

        assert isinstance(defs, Definitions)
        assert len(list(defs.assets or [])) == 0


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

from phlo.ingestion import phlo_ingestion
from dlt.sources.rest_api import rest_api


@phlo_ingestion(
    table_name="test_data",
    unique_key="id",
    group="test",
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
        defs = build_definitions(
            workflows_path=workflows_path, include_core_assets=False
        )

        assert isinstance(defs, Definitions)
        # Should at least have resources
        assert defs.resources is not None


def test_build_definitions_without_workflows_path():
    """Test that build_definitions handles missing workflows gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = Path(tmpdir) / "nonexistent"

        # Should not raise, just log warning
        defs = build_definitions(workflows_path=non_existent, include_core_assets=False)

        assert isinstance(defs, Definitions)


def test_project_type_detection():
    """Test detection of user project vs Cascade repo."""
    from phlo.cli.scaffold import _is_user_project

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Empty directory - should be Cascade repo mode (no workflows)
        assert not _is_user_project(project_root)

        # Add workflows directory - should be user project
        (project_root / "workflows").mkdir()
        assert _is_user_project(project_root)

        # Add both workflows and src/phlo - check pyproject.toml
        (project_root / "src" / "phlo").mkdir(parents=True)

        # User project (has phlo as dependency)
        (project_root / "pyproject.toml").write_text(
            '[project]\nname = "my-project"\ndependencies = ["phlo"]'
        )
        assert _is_user_project(project_root)

        # Cascade repo (has name = "phlo")
        (project_root / "pyproject.toml").write_text(
            '[project]\nname = "phlo"\ndependencies = []'
        )
        assert not _is_user_project(project_root)


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
        assert (project_dir / "transforms" / "dbt").is_dir()
        assert (project_dir / "transforms" / "dbt" / "dbt_project.yml").exists()
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
        assert not (project_dir / "transforms").exists()
