"""Tests for Nessie table scanner."""

from unittest.mock import Mock, patch

import pytest
import requests

from phlo.catalog.nessie import NessieTableScanner
from phlo.catalog.openmetadata import OpenMetadataTable


@pytest.fixture
def nessie_scanner():
    """Create Nessie scanner for testing."""
    return NessieTableScanner(nessie_uri="http://nessie:19120/api/v1")


class TestNessieTableScanner:
    """Tests for NessieTableScanner."""

    def test_scanner_initialization(self, nessie_scanner):
        """Test scanner initialization."""
        assert nessie_scanner.nessie_uri == "http://nessie:19120/api/v1"
        assert nessie_scanner.timeout == 30

    def test_base_uri_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URI."""
        scanner = NessieTableScanner(nessie_uri="http://nessie:19120/api/v1/")
        assert scanner.nessie_uri == "http://nessie:19120/api/v1"

    @patch("phlo.catalog.nessie.requests.request")
    def test_list_namespaces(self, mock_request, nessie_scanner):
        """Test listing namespaces."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "namespaces": [
                {"namespace": ["bronze"]},
                {"namespace": ["silver"]},
                {"namespace": ["gold"]},
            ]
        }
        mock_request.return_value = mock_response

        result = nessie_scanner.list_namespaces()

        assert len(result) == 3
        assert result[0]["namespace"] == ["bronze"]

    @patch("phlo.catalog.nessie.requests.request")
    def test_list_tables_in_namespace(self, mock_request, nessie_scanner):
        """Test listing tables in a namespace."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tables": [
                {"name": "glucose_entries"},
                {"name": "glucose_readings"},
            ]
        }
        mock_request.return_value = mock_response

        result = nessie_scanner.list_tables_in_namespace("bronze")

        assert len(result) == 2
        assert result[0]["name"] == "glucose_entries"

    @patch("phlo.catalog.nessie.requests.request")
    def test_list_tables_with_list_namespace(self, mock_request, nessie_scanner):
        """Test listing tables with namespace as list."""
        mock_response = Mock()
        mock_response.json.return_value = {"tables": []}
        mock_request.return_value = mock_response

        nessie_scanner.list_tables_in_namespace(["bronze", "sub"])

        # Check that namespace was joined with dots
        call_args = mock_request.call_args
        assert "bronze.sub" in str(call_args)

    @patch("phlo.catalog.nessie.requests.request")
    def test_get_table_metadata(self, mock_request, nessie_scanner):
        """Test getting table metadata."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "glucose_entries",
            "schema": {
                "fields": [
                    {"name": "id", "type": "long"},
                    {"name": "timestamp", "type": "timestamp"},
                    {"name": "value", "type": "double"},
                ]
            },
            "properties": {"location": "s3://lake/warehouse/bronze/glucose_entries"},
        }
        mock_request.return_value = mock_response

        result = nessie_scanner.get_table_metadata("bronze", "glucose_entries")

        assert result["name"] == "glucose_entries"
        assert len(result["schema"]["fields"]) == 3

    @patch("phlo.catalog.nessie.requests.request")
    def test_get_table_metadata_not_found(self, mock_request, nessie_scanner):
        """Test getting non-existent table metadata."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("Not found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_request.return_value = mock_response

        result = nessie_scanner.get_table_metadata("bronze", "nonexistent")

        assert result is None

    def test_map_iceberg_to_om_type(self):
        """Test Iceberg to OpenMetadata type mapping."""
        assert NessieTableScanner._map_iceberg_to_om_type("boolean") == "BOOLEAN"
        assert NessieTableScanner._map_iceberg_to_om_type("int") == "INT"
        assert NessieTableScanner._map_iceberg_to_om_type("long") == "LONG"
        assert NessieTableScanner._map_iceberg_to_om_type("float") == "FLOAT"
        assert NessieTableScanner._map_iceberg_to_om_type("double") == "DOUBLE"
        assert NessieTableScanner._map_iceberg_to_om_type("string") == "STRING"
        assert NessieTableScanner._map_iceberg_to_om_type("date") == "DATE"
        assert NessieTableScanner._map_iceberg_to_om_type("timestamp") == "TIMESTAMP"

    def test_map_iceberg_complex_types(self):
        """Test mapping complex Iceberg types."""
        assert NessieTableScanner._map_iceberg_to_om_type("list<int>") == "ARRAY"
        assert NessieTableScanner._map_iceberg_to_om_type("struct<...>") == "STRUCT"
        assert NessieTableScanner._map_iceberg_to_om_type("map<...>") == "MAP"
        assert NessieTableScanner._map_iceberg_to_om_type("unknown_type") == "UNKNOWN"

    def test_extract_openmetadata_table(self, nessie_scanner):
        """Test extracting OpenMetadata table from Nessie metadata."""
        table_metadata = {
            "name": "glucose_entries",
            "doc": "Glucose sensor readings",
            "schema": {
                "fields": [
                    {"name": "id", "type": "long"},
                    {"name": "value", "type": "double"},
                ]
            },
            "properties": {"location": "s3://lake/warehouse/bronze/glucose_entries"},
        }

        om_table = nessie_scanner.extract_openmetadata_table(
            "bronze", table_metadata
        )

        assert om_table.name == "glucose_entries"
        assert om_table.description == "Glucose sensor readings"
        assert len(om_table.columns) == 2
        assert om_table.columns[0].name == "id"
        assert om_table.columns[0].dataType == "LONG"
        assert om_table.location == "s3://lake/warehouse/bronze/glucose_entries"

    @patch.object(NessieTableScanner, "scan_all_tables")
    @patch("phlo.catalog.nessie.NessieTableScanner.extract_openmetadata_table")
    def test_sync_to_openmetadata(
        self,
        mock_extract,
        mock_scan,
        nessie_scanner,
    ):
        """Test syncing tables to OpenMetadata."""
        # Mock scan results
        mock_scan.return_value = {
            "bronze": [
                {"name": "glucose_entries", "schema": {"fields": []}},
                {"name": "weather_data", "schema": {"fields": []}},
            ]
        }

        # Mock extracted tables
        mock_table = Mock(spec=OpenMetadataTable)
        mock_extract.return_value = mock_table

        # Mock OpenMetadata client
        om_client = Mock()
        om_client.create_or_update_table.return_value = {"id": "123"}

        # Perform sync
        stats = nessie_scanner.sync_to_openmetadata(om_client)

        assert stats["created"] == 2
        assert stats["failed"] == 0
        assert om_client.create_or_update_table.call_count == 2

    @patch.object(NessieTableScanner, "scan_all_tables")
    def test_sync_with_namespace_filtering(self, mock_scan, nessie_scanner):
        """Test syncing with namespace filtering."""
        mock_scan.return_value = {
            "bronze": [{"name": "table1", "schema": {"fields": []}}],
            "silver": [{"name": "table2", "schema": {"fields": []}}],
            "gold": [{"name": "table3", "schema": {"fields": []}}],
        }

        om_client = Mock()

        # Include only bronze and silver
        nessie_scanner.sync_to_openmetadata(
            om_client,
            include_namespaces=["bronze", "silver"],
        )

        # Should have called create_or_update_table twice (bronze + silver)
        assert om_client.create_or_update_table.call_count == 2

    @patch.object(NessieTableScanner, "scan_all_tables")
    def test_sync_with_namespace_exclusion(self, mock_scan, nessie_scanner):
        """Test syncing with namespace exclusion."""
        mock_scan.return_value = {
            "bronze": [{"name": "table1", "schema": {"fields": []}}],
            "silver": [{"name": "table2", "schema": {"fields": []}}],
            "gold": [{"name": "table3", "schema": {"fields": []}}],
        }

        om_client = Mock()

        # Exclude gold
        nessie_scanner.sync_to_openmetadata(
            om_client,
            exclude_namespaces=["gold"],
        )

        # Should have called create_or_update_table twice (bronze + silver)
        assert om_client.create_or_update_table.call_count == 2

    @patch("phlo.catalog.nessie.requests.request")
    def test_request_error_handling(self, mock_request, nessie_scanner):
        """Test error handling in _request."""
        mock_request.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(requests.ConnectionError):
            nessie_scanner._request("GET", "/namespaces")

    @patch.object(NessieTableScanner, "scan_all_tables")
    def test_sync_partial_failure(self, mock_scan, nessie_scanner):
        """Test sync with partial failures."""
        mock_scan.return_value = {
            "bronze": [
                {"name": "table1", "schema": {"fields": []}},
                {"name": "table2", "schema": {"fields": []}},
            ]
        }

        om_client = Mock()
        # First call succeeds, second fails
        om_client.create_or_update_table.side_effect = [
            {"id": "1"},
            Exception("Sync error"),
        ]

        stats = nessie_scanner.sync_to_openmetadata(om_client)

        assert stats["created"] == 1
        assert stats["failed"] == 1
