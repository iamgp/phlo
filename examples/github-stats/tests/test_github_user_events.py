"""
Tests for github user_events workflow.
"""

import pandas as pd

from workflows.schemas.github import RawUserEvents


class TestSchema:
    """Test Pandera schema validation."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""

        test_data = pd.DataFrame(
            [
                {
                    "id": "test-001",
                    # TODO: Add test data for your fields
                },
            ]
        )

        # Should not raise
        validated = RawUserEvents.validate(test_data)
        assert len(validated) == 1
        assert validated["id"].iloc[0] == "test-001"

    def test_unique_key_field_exists(self):
        """Test that unique_key field exists in schema."""

        schema_fields = RawUserEvents.to_schema().columns.keys()
        assert "id" in schema_fields, f"unique_key 'id' not found. Available: {list(schema_fields)}"

    # TODO: Add more schema tests
    # def test_invalid_data_fails_validation(self):
    #     """Test that invalid data fails validation."""
    #     test_data = pd.DataFrame([{
    #         "id": "test",
    #         "value": -10,  # Violates constraints
    #     }])
    #
    #     with pytest.raises(Exception):
    #         RawUserEvents.validate(test_data)


# TODO: Add asset execution tests
# from phlo.testing import test_asset_execution
# from phlo.defs.ingestion.github.user_events import user_events
#
# def test_asset_with_mock_data():
#     """Test asset execution with mock data."""
#     test_data = [{"
#         "id": "1",
#         # Add fields
#     }]
#
#     result = test_asset_execution(
#         asset_fn=user_events,
#         partition="2024-01-15",
#         mock_data=test_data,
#         validation_schema=RawUserEvents,
#     )
#
#     assert result.success
#     assert len(result.data) == 1
