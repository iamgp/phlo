"""
Ingestion Asset Test Template

This template shows how to test Cascade ingestion assets.

TODO: Customize this template:
1. Copy to tests/test_YOUR_DOMAIN_YOUR_ASSET.py
2. Update imports to match your asset and schema
3. Customize test data to match your schema
4. Add additional tests as needed
"""

import pytest
import pandas as pd

# TODO: Update these imports to match your asset and schema
# Example:
# from cascade.defs.ingestion.weather.observations import weather_observations
# from cascade.schemas.weather import RawWeatherData
from cascade.defs.ingestion.example.data import example_data_ingestion
from cascade.schemas.example import RawExampleData


class TestSchemaValidation:
    """Test Pandera schema validation."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""

        # TODO: Create test data that matches your schema
        test_data = pd.DataFrame([
            {
                "id": "test-001",
                "timestamp": "2024-01-15T12:00:00.000Z",
                "name": "Test Record",
                "value": 42.5,
                "count": 10,
                "is_active": True,
                "notes": "Test note",
            },
            {
                "id": "test-002",
                "timestamp": "2024-01-15T13:00:00.000Z",
                "name": "Another Record",
                "value": 100.0,
                "count": 5,
                "is_active": False,
                "notes": None,  # Testing nullable field
            },
        ])

        # Validate against schema (should not raise)
        validated = RawExampleData.validate(test_data)

        assert len(validated) == 2
        assert validated["id"].tolist() == ["test-001", "test-002"]

    def test_invalid_data_fails_validation(self):
        """Test that invalid data fails schema validation."""

        # TODO: Create test data that violates your schema constraints
        test_data = pd.DataFrame([
            {
                "id": "test-001",
                "timestamp": "2024-01-15T12:00:00.000Z",
                "name": "Test Record",
                "value": -10.0,  # Invalid: should be >= 0
                "count": 5,
                "is_active": True,
            },
        ])

        # Should raise SchemaError
        with pytest.raises(Exception):  # Pandera raises SchemaError
            RawExampleData.validate(test_data)

    def test_schema_has_required_fields(self):
        """Test that schema includes expected fields."""

        schema_fields = RawExampleData.to_schema().columns.keys()

        # TODO: Update with your actual required fields
        required_fields = ["id", "timestamp", "name", "value", "count", "is_active"]

        for field in required_fields:
            assert field in schema_fields, f"Missing required field: {field}"

    def test_unique_key_field_exists(self):
        """Test that the unique_key field exists in schema."""

        schema_fields = RawExampleData.to_schema().columns.keys()

        # TODO: Update with your actual unique_key (must match decorator)
        unique_key = "id"

        assert unique_key in schema_fields, \
            f"unique_key '{unique_key}' not found in schema. Available: {list(schema_fields)}"


class TestAssetConfiguration:
    """Test asset decorator configuration."""

    def test_asset_has_correct_table_name(self):
        """Test that asset is configured with correct table name."""

        # TODO: Update expected table name
        # Check the asset's op name (prefixed with 'dlt_')
        assert example_data_ingestion.op.name == "dlt_example_data"

    def test_asset_has_partition_parameter(self):
        """Test that asset function accepts partition_date parameter."""

        import inspect

        sig = inspect.signature(example_data_ingestion.op.compute_fn)
        params = sig.parameters

        # Should have 'partition_date' parameter (and 'context' from decorator)
        assert "partition_date" in params, "Asset must accept partition_date parameter"


class TestAssetExecution:
    """
    Test asset execution.

    Note: These tests require mocking DLT, Iceberg, and Dagster context.
    In production, consider using cascade.testing utilities (when available).
    """

    @pytest.mark.skip(reason="Requires full Docker stack or extensive mocking")
    def test_asset_execution_with_test_data(self):
        """
        Test asset execution with mocked dependencies.

        TODO: Implement once cascade.testing module is available:

        from cascade.testing import mock_dlt_source, mock_iceberg_catalog

        def test_execution():
            with mock_dlt_source(data=[...]) as source:
                with mock_iceberg_catalog() as catalog:
                    result = example_data_ingestion("2024-01-15")
                    assert result.success
                    assert result.rows_written > 0
        """
        pass

    @pytest.mark.skip(reason="Requires Docker infrastructure")
    def test_integration_full_pipeline(self):
        """
        Test full pipeline end-to-end.

        This test requires:
        - Docker services running (Nessie, MinIO, Trino)
        - Valid API credentials
        - Network connectivity

        Run with: pytest tests/test_example.py::TestAssetExecution::test_integration_full_pipeline
        """
        pass


class TestDataTransformations:
    """Test any data transformations in your asset."""

    def test_date_formatting(self):
        """Test that dates are formatted correctly for API."""

        partition_date = "2024-01-15"

        # Example: Test date conversion logic
        start_time = f"{partition_date}T00:00:00.000Z"
        end_time = f"{partition_date}T23:59:59.999Z"

        assert start_time == "2024-01-15T00:00:00.000Z"
        assert end_time == "2024-01-15T23:59:59.999Z"

    # TODO: Add tests for any business logic in your asset
    # Examples:
    # - Data filtering
    # - Field calculations
    # - Type conversions
    # - Data enrichment


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.skip(reason="Requires mocking")
    def test_handles_api_timeout_gracefully(self):
        """Test that API timeouts are handled gracefully."""
        # TODO: Mock API timeout and verify retry behavior
        pass

    @pytest.mark.skip(reason="Requires mocking")
    def test_handles_invalid_response_format(self):
        """Test that invalid API response format is handled."""
        # TODO: Mock invalid response and verify error handling
        pass


# Fixtures
# ========

@pytest.fixture
def sample_valid_data():
    """
    Fixture providing sample valid data for tests.

    TODO: Customize to match your schema.
    """
    return pd.DataFrame([
        {
            "id": "fixture-001",
            "timestamp": "2024-01-15T12:00:00.000Z",
            "name": "Fixture Record 1",
            "value": 50.0,
            "count": 5,
            "is_active": True,
            "notes": "From fixture",
        },
        {
            "id": "fixture-002",
            "timestamp": "2024-01-15T13:00:00.000Z",
            "name": "Fixture Record 2",
            "value": 75.0,
            "count": 10,
            "is_active": True,
            "notes": None,
        },
    ])


@pytest.fixture
def sample_invalid_data():
    """
    Fixture providing sample invalid data for testing validation errors.

    TODO: Customize to include constraint violations for your schema.
    """
    return pd.DataFrame([
        {
            "id": "invalid-001",
            "timestamp": "2024-01-15T12:00:00.000Z",
            "name": "Invalid Record",
            "value": -100.0,  # Violates ge=0 constraint
            "count": -5,  # Violates ge=0 constraint
            "is_active": True,
        },
    ])


# Usage Examples:
# ===============
#
# Run all tests:
#   pytest tests/test_example.py -v
#
# Run specific test class:
#   pytest tests/test_example.py::TestSchemaValidation -v
#
# Run specific test:
#   pytest tests/test_example.py::TestSchemaValidation::test_valid_data_passes_validation -v
#
# Run with coverage:
#   pytest tests/test_example.py --cov=cascade --cov-report=html
#
# Run integration tests only (requires Docker):
#   pytest tests/test_example.py -m integration -v


# Best Practices:
# ===============
#
# 1. TEST SCHEMA FIRST
#    - Validate schema with known good data
#    - Test constraint violations
#    - Verify unique_key exists
#
# 2. USE FIXTURES
#    - Create reusable test data fixtures
#    - Keep fixtures small and focused
#    - Store complex fixtures in separate files
#
# 3. MOCK EXTERNAL DEPENDENCIES
#    - Mock API calls
#    - Mock database connections
#    - Mock file system operations
#
# 4. SEPARATE UNIT AND INTEGRATION TESTS
#    - Unit tests: Fast, no dependencies (schema validation, data transformations)
#    - Integration tests: Slow, requires Docker (full pipeline execution)
#    - Mark integration tests: @pytest.mark.integration
#
# 5. TEST ERROR CASES
#    - Invalid data
#    - API failures
#    - Network timeouts
#    - Missing credentials
#
# 6. KEEP TESTS MAINTAINABLE
#    - Clear test names (test_WHAT_WHEN_EXPECTED)
#    - One assertion concept per test
#    - Use fixtures to reduce duplication
#    - Add comments explaining complex test logic


# Next Steps:
# ===========
#
# 1. Copy this template:
#    cp templates/tests/test_ingestion.py tests/test_YOUR_DOMAIN.py
#
# 2. Update imports to match your asset and schema
#
# 3. Customize test data to match your schema
#
# 4. Run tests:
#    pytest tests/test_YOUR_DOMAIN.py -v
#
# 5. Add to CI/CD pipeline:
#    - Run on every commit
#    - Require passing tests for merge
#    - Track test coverage
#
# 6. Expand test coverage:
#    - Add integration tests when cascade.testing is available
#    - Test edge cases and error conditions
#    - Test data transformations and business logic
