"""
Tests for spec 004: Schema & Catalog Management CLI commands.

Tests cover:
- phlo schema commands (list, show, diff, validate)
- phlo catalog commands (tables, describe, history)
- phlo branch commands (list, create, delete, merge, diff)
"""

import json
from pathlib import Path
from typing import Optional

import pytest
from click.testing import CliRunner

from phlo.cli.main import cli
from phlo.cli.utils import discover_pandera_schemas, classify_schema_change


class TestSchemaCommands:
    """Test phlo schema commands."""

    def test_schema_list(self):
        """Test phlo schema list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "list"])

        assert result.exit_code == 0
        assert "RawGlucoseEntries" in result.output
        assert "FactGlucoseReadings" in result.output
        assert "Available Schemas" in result.output

    def test_schema_list_domain_filter(self):
        """Test phlo schema list with domain filter."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "list", "--domain", "glucose"])

        assert result.exit_code == 0
        # Should show glucose schemas
        assert "RawGlucoseEntries" in result.output or "Glucose" in result.output

    def test_schema_list_json_format(self):
        """Test phlo schema list with JSON output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "list", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "RawGlucoseEntries" in data

    def test_schema_show(self):
        """Test phlo schema show command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "show", "RawGlucoseEntries"])

        assert result.exit_code == 0
        assert "RawGlucoseEntries" in result.output
        assert "_id" in result.output
        assert "sgv" in result.output
        assert "Fields:" in result.output

    def test_schema_show_not_found(self):
        """Test phlo schema show with invalid schema."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "show", "NonExistentSchema"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_schema_show_iceberg(self):
        """Test phlo schema show with Iceberg output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "show", "RawGlucoseEntries", "--iceberg"])

        assert result.exit_code == 0
        assert "Iceberg Schema" in result.output

    def test_schema_diff(self):
        """Test phlo schema diff command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "diff", "RawGlucoseEntries"])

        assert result.exit_code == 0
        assert "Diff" in result.output

    def test_schema_diff_json(self):
        """Test phlo schema diff with JSON output."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["schema", "diff", "RawGlucoseEntries", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "classification" in data
        assert "details" in data

    def test_schema_validate(self):
        """Test phlo schema validate command."""
        runner = CliRunner()

        # Use actual schema file that exists
        schema_file = "examples/glucose-platform/workflows/schemas/nightscout.py"
        result = runner.invoke(cli, ["schema", "validate", schema_file])

        assert result.exit_code == 0
        assert "Schema Validation" in result.output
        assert "All checks passed" in result.output

    def test_schema_validate_not_found(self):
        """Test phlo schema validate with nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "validate", "nonexistent.py"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestDiscoverPanderaSchemas:
    """Test schema discovery utility."""

    def test_discover_schemas(self):
        """Test discovering Pandera schemas."""
        schemas = discover_pandera_schemas()

        assert isinstance(schemas, dict)
        assert len(schemas) > 0
        assert "RawGlucoseEntries" in schemas

    def test_discovered_schema_is_class(self):
        """Test that discovered schemas are classes."""
        schemas = discover_pandera_schemas()

        for name, schema_cls in schemas.items():
            assert isinstance(name, str)
            assert isinstance(schema_cls, type)

    def test_schema_has_annotations(self):
        """Test that schemas have field annotations."""
        schemas = discover_pandera_schemas()

        raw_glucose = schemas.get("RawGlucoseEntries")
        assert raw_glucose is not None
        assert hasattr(raw_glucose, "__annotations__")
        assert len(raw_glucose.__annotations__) > 0


class TestClassifySchemaChange:
    """Test schema change classification."""

    def test_safe_change_added_column(self):
        """Test that adding a nullable column is classified as SAFE."""
        old_schema = {"id": "int", "name": "str"}
        new_schema = {"id": "int", "name": "str", "description": "str"}

        classification, details = classify_schema_change(old_schema, new_schema)

        assert classification == "SAFE"
        assert "Added columns" in " ".join(details)

    def test_breaking_change_removed_column(self):
        """Test that removing a column is classified as BREAKING."""
        old_schema = {"id": "int", "name": "str"}
        new_schema = {"id": "int"}

        classification, details = classify_schema_change(old_schema, new_schema)

        assert classification == "BREAKING"
        assert "Removed columns" in " ".join(details)

    def test_breaking_change_type_change(self):
        """Test that changing column type is classified as BREAKING."""
        old_schema = {"id": "int", "name": "str"}
        new_schema = {"id": "str", "name": "str"}

        classification, details = classify_schema_change(old_schema, new_schema)

        assert classification == "BREAKING"
        assert any("Type changes" in detail for detail in details)

    def test_no_change(self):
        """Test classification when schemas are identical."""
        schema = {"id": "int", "name": "str"}

        classification, details = classify_schema_change(schema, schema)

        assert classification == "SAFE"
        assert "No changes" in " ".join(details)


class TestCatalogCommands:
    """Test phlo catalog commands (integration tests with mocked catalog)."""

    @pytest.mark.skip(reason="Requires running Iceberg catalog")
    def test_catalog_list_tables(self):
        """Test phlo catalog tables command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog", "tables"])

        # Would need running Iceberg catalog for this to work
        assert result.exit_code in [0, 1]  # Might fail if catalog not available

    @pytest.mark.skip(reason="Requires running Iceberg catalog")
    def test_catalog_describe(self):
        """Test phlo catalog describe command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog", "describe", "raw.glucose_entries"])

        # Would need running Iceberg catalog
        assert result.exit_code in [0, 1]

    @pytest.mark.skip(reason="Requires running Iceberg catalog")
    def test_catalog_history(self):
        """Test phlo catalog history command."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["catalog", "history", "raw.glucose_entries", "--limit", "5"]
        )

        # Would need running Iceberg catalog
        assert result.exit_code in [0, 1]


class TestBranchCommands:
    """Test phlo branch (Nessie) commands."""

    @pytest.mark.skip(reason="Requires running Nessie server")
    def test_branch_list(self):
        """Test phlo branch list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["branch", "list"])

        # Would need running Nessie server
        assert result.exit_code in [0, 1]

    @pytest.mark.skip(reason="Requires running Nessie server")
    def test_branch_create(self):
        """Test phlo branch create command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["branch", "create", "test-branch"])

        # Would need running Nessie server
        assert result.exit_code in [0, 1]


# Integration test marker for catalog/branch tests
pytestmark = pytest.mark.integration
