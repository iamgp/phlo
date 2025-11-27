"""Tests for PostgREST view generation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from phlo.api.postgrest.views import (
    DbtManifestParser,
    DbtModel,
    PostgreSTViewManager,
    ViewGenerator,
    generate_views,
)


@pytest.fixture
def sample_manifest():
    """Create a sample dbt manifest for testing."""
    return {
        "nodes": {
            "model.phlo.glucose_readings": {
                "name": "glucose_readings",
                "schema": "marts",
                "description": "Curated glucose readings",
                "tags": ["api", "analyst"],
                "columns": {
                    "reading_id": {"name": "reading_id", "description": "Unique ID"},
                    "timestamp": {"name": "timestamp", "description": "Reading time"},
                    "sgv": {"name": "sgv", "description": "Blood glucose value"},
                },
                "depends_on": {"nodes": []},
            },
            "model.phlo.glucose_metrics": {
                "name": "glucose_metrics",
                "schema": "marts",
                "description": "Daily glucose metrics",
                "tags": ["api", "public"],
                "columns": {
                    "metric_date": {"name": "metric_date"},
                    "avg_sgv": {"name": "avg_sgv"},
                },
                "depends_on": {
                    "nodes": ["model.phlo.glucose_readings"]
                },
            },
            "model.phlo.bronze_raw_data": {
                "name": "bronze_raw_data",
                "schema": "bronze",
                "description": "Raw data",
                "tags": [],
                "columns": {},
                "depends_on": {"nodes": []},
            },
            "source.some_source": {
                "name": "some_source",
                "source_name": "external",
            },
        }
    }


@pytest.fixture
def manifest_file(tmp_path, sample_manifest):
    """Create a temporary manifest file."""
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(sample_manifest, f)
    return str(manifest_path)


class TestDbtManifestParser:
    """Tests for DbtManifestParser."""

    def test_parse_extracts_marts_models(self, manifest_file):
        """Should extract only models from marts schema."""
        parser = DbtManifestParser(manifest_file)
        models = parser.parse()

        assert "glucose_readings" in models
        assert "glucose_metrics" in models
        assert "bronze_raw_data" not in models
        assert len(models) == 2

    def test_parse_extracts_model_metadata(self, manifest_file):
        """Should extract all model metadata."""
        parser = DbtManifestParser(manifest_file)
        models = parser.parse()

        model = models["glucose_readings"]
        assert model.name == "glucose_readings"
        assert model.schema == "marts"
        assert model.description == "Curated glucose readings"
        assert model.tags == ["api", "analyst"]
        assert "reading_id" in model.columns

    def test_build_dependency_graph(self, manifest_file):
        """Should build correct dependency graph."""
        parser = DbtManifestParser(manifest_file)
        graph = parser.build_dependency_graph()

        assert "glucose_readings" in graph
        assert "glucose_metrics" in graph
        assert graph["glucose_metrics"] == ["glucose_readings"]
        assert graph["glucose_readings"] == []


class TestViewGenerator:
    """Tests for ViewGenerator."""

    def test_generate_view_sql(self, manifest_file):
        """Should generate valid CREATE VIEW SQL."""
        generator = ViewGenerator(manifest_file)
        models = generator.parser.parse()
        model = models["glucose_readings"]

        sql = generator.generate_view_sql(model)

        assert "CREATE OR REPLACE VIEW api.glucose_readings" in sql
        assert "FROM marts.glucose_readings" in sql
        assert "reading_id" in sql
        assert "timestamp" in sql
        assert "sgv" in sql
        assert "COMMENT ON VIEW" in sql

    def test_generate_permissions_sql(self, manifest_file):
        """Should generate correct GRANT statements."""
        generator = ViewGenerator(manifest_file)
        models = generator.parser.parse()
        model = models["glucose_readings"]

        sql = generator.generate_permissions_sql(model)

        # analyst and admin tags should grant to analyst and admin
        assert "GRANT SELECT ON api.glucose_readings TO analyst" in sql
        assert "GRANT SELECT ON api.glucose_readings TO admin" in sql
        assert "CREATE POLICY analyst_access" in sql
        assert "CREATE POLICY admin_access" in sql

    def test_generate_permissions_with_public_tag(self, manifest_file):
        """Should grant to anon role for public tag."""
        generator = ViewGenerator(manifest_file)
        models = generator.parser.parse()
        model = models["glucose_metrics"]

        sql = generator.generate_permissions_sql(model)

        # public tag should grant to anon, analyst, and admin roles
        assert "GRANT SELECT ON api.glucose_metrics TO anon" in sql
        assert "CREATE POLICY anon_access" in sql

    def test_generate_all_views(self, manifest_file):
        """Should generate SQL for all views."""
        generator = ViewGenerator(manifest_file)
        sql = generator.generate_all_views()

        assert "glucose_readings" in sql
        assert "glucose_metrics" in sql
        assert sql.count("CREATE OR REPLACE VIEW") == 2

    def test_generate_all_views_with_filter(self, manifest_file):
        """Should filter models by pattern."""
        generator = ViewGenerator(manifest_file)
        sql = generator.generate_all_views(model_filter="glucose_readings")

        assert "glucose_readings" in sql
        assert "glucose_metrics" not in sql
        assert sql.count("CREATE OR REPLACE VIEW") == 1

    def test_topological_sort(self, manifest_file):
        """Should sort models by dependencies."""
        generator = ViewGenerator(manifest_file)
        models = generator.parser.parse()
        graph = generator.parser.build_dependency_graph()

        sorted_models = generator._topological_sort(models, graph)

        # glucose_readings should come before glucose_metrics
        assert sorted_models.index("glucose_readings") < sorted_models.index(
            "glucose_metrics"
        )

    def test_escape_string(self):
        """Should escape single quotes in strings."""
        escaped = ViewGenerator._escape_string("It's a test")
        assert escaped == "It''s a test"


class TestPostgreSQLViewManager:
    """Tests for PostgreSTViewManager."""

    @patch("phlo.api.postgrest.views.psycopg2.connect")
    def test_execute_sql(self, mock_connect):
        """Should execute SQL statements."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        manager = PostgreSTViewManager()
        manager.execute_sql("SELECT 1;")

        mock_cursor.execute.assert_called_once_with("SELECT 1;")

    @patch("phlo.api.postgrest.views.psycopg2.connect")
    def test_get_existing_views(self, mock_connect):
        """Should retrieve existing views from schema."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.fetchall.return_value = [
            ("glucose_readings",),
            ("glucose_metrics",),
        ]

        manager = PostgreSTViewManager()
        views = manager.get_existing_views()

        assert views == {"glucose_readings", "glucose_metrics"}

    @patch("phlo.api.postgrest.views.psycopg2.connect")
    def test_generate_diff(self, mock_connect):
        """Should generate diff of new vs existing views."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connect
        mock_connect.cursor.return_value = mock_cursor

        # glucose_readings already exists, so it should show as updated
        mock_cursor.fetchall.return_value = [
            ("old_view",),
            ("glucose_readings",),
        ]

        manager = PostgreSTViewManager()
        new_sql = """
        CREATE OR REPLACE VIEW api.new_view AS SELECT 1;
        CREATE OR REPLACE VIEW api.glucose_readings AS SELECT * FROM marts.glucose_readings;
        """

        diff = manager.generate_diff(new_sql)

        assert "new_view (new)" in diff
        assert "glucose_readings (updated)" in diff
        assert "old_view (orphaned)" in diff


class TestGenerateViewsFunction:
    """Tests for the main generate_views function."""

    def test_generate_views_returns_sql(self, manifest_file):
        """Should return SQL when no output specified."""
        sql = generate_views(manifest_path=manifest_file, verbose=False)

        assert sql.startswith("-- PostgREST API Views")
        assert "CREATE OR REPLACE VIEW" in sql

    def test_generate_views_writes_file(self, manifest_file, tmp_path):
        """Should write SQL to output file."""
        output_file = tmp_path / "views.sql"

        result = generate_views(
            manifest_path=manifest_file,
            output=str(output_file),
            verbose=False,
        )

        assert output_file.exists()
        assert "SQL written to" in result

    @patch("phlo.api.postgrest.views.PostgreSTViewManager.execute_sql")
    def test_generate_views_apply(self, mock_execute, manifest_file):
        """Should execute SQL when apply=True."""
        result = generate_views(
            manifest_path=manifest_file,
            apply=True,
            verbose=False,
        )

        mock_execute.assert_called_once()
        assert "applied successfully" in result

    @patch("phlo.api.postgrest.views.PostgreSTViewManager.generate_diff")
    def test_generate_views_diff(self, mock_diff, manifest_file):
        """Should show diff when diff=True."""
        mock_diff.return_value = "Diff summary"

        result = generate_views(
            manifest_path=manifest_file,
            diff=True,
            verbose=False,
        )

        assert "Diff summary" in result
        mock_diff.assert_called_once()
