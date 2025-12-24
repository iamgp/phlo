"""
Tests for github user_events workflow.

Demonstrates phlo_testing fixtures for testing ingestion workflows
without Docker dependencies.
"""

import pandas as pd
import pytest
from workflows.schemas.github import RawUserEvents


class TestSchemaValidation:
    """Test Pandera schema validation for RawUserEvents."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""
        test_data = pd.DataFrame(
            [
                {
                    "id": "evt_12345678",
                    "type": "PushEvent",
                    "created_at": "2024-01-15T10:30:00Z",
                    "actor__login": "octocat",
                    "repo__name": "octocat/hello-world",
                },
                {
                    "id": "evt_87654321",
                    "type": "PullRequestEvent",
                    "created_at": "2024-01-15T11:00:00Z",
                    "actor__login": "octocat",
                    "repo__name": "octocat/hello-world",
                },
            ]
        )

        # Should not raise
        validated = RawUserEvents.validate(test_data)
        assert len(validated) == 2
        assert validated["id"].iloc[0] == "evt_12345678"
        assert validated["type"].iloc[1] == "PullRequestEvent"

    def test_unique_key_field_exists(self):
        """Test that unique_key field (id) exists in schema."""
        schema_fields = RawUserEvents.to_schema().columns.keys()
        assert "id" in schema_fields, f"unique_key 'id' not found. Available: {list(schema_fields)}"

    def test_nullable_fields_accept_none(self):
        """Test that str | None fields properly accept None values.

        PhloSchema auto-infers nullable=True from Optional type hints,
        so fields like `actor__login: str | None` will accept None.
        """
        test_data = pd.DataFrame(
            [
                {
                    "id": "evt_null_test",
                    "type": "IssuesEvent",
                    "created_at": "2024-01-15T12:00:00Z",
                    "actor__login": None,  # Nullable field
                    "repo__name": None,  # Nullable field
                },
            ]
        )

        validated = RawUserEvents.validate(test_data)
        assert len(validated) == 1
        assert pd.isna(validated["actor__login"].iloc[0])
        assert pd.isna(validated["repo__name"].iloc[0])

    def test_invalid_duplicate_ids_fails(self):
        """Test that duplicate IDs fail validation (unique constraint)."""
        test_data = pd.DataFrame(
            [
                {
                    "id": "duplicate_id",
                    "type": "PushEvent",
                    "created_at": "2024-01-15T10:00:00Z",
                    "actor__login": "user1",
                    "repo__name": "repo1",
                },
                {
                    "id": "duplicate_id",  # Duplicate!
                    "type": "PushEvent",
                    "created_at": "2024-01-15T11:00:00Z",
                    "actor__login": "user2",
                    "repo__name": "repo2",
                },
            ]
        )

        with pytest.raises(Exception):  # Pandera raises SchemaError
            RawUserEvents.validate(test_data)


class TestWithFixtures:
    """Tests demonstrating phlo_testing fixtures."""

    def test_with_partition_date(self, sample_partition_date):
        """Test using sample_partition_date fixture."""
        # Fixture provides a standard date for testing
        assert sample_partition_date == "2024-01-15"

    def test_with_mock_catalog(self, mock_iceberg_catalog):
        """Test using mock_iceberg_catalog fixture."""
        # Can create tables without Docker/real Iceberg
        # MockIcebergCatalog accepts dict schema: {"col_name": "type"}
        schema = {"id": "string", "type": "string"}
        table = mock_iceberg_catalog.create_table(
            identifier="raw.test_events",
            schema=schema,
        )
        assert table is not None

    def test_with_mock_trino(self, mock_trino):
        """Test using mock_trino fixture (DuckDB-backed)."""
        cursor = mock_trino.cursor()
        cursor.execute("SELECT 1 as id, 'test' as name")
        result = cursor.fetchall()
        assert result == [(1, "test")]

    def test_with_sample_dlt_data(self, sample_dlt_data):
        """Test using sample_dlt_data fixture."""
        # Fixture provides sample records for DLT source mocking
        assert len(sample_dlt_data) == 3
        assert "id" in sample_dlt_data[0]
