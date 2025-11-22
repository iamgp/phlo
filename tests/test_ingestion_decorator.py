"""Tests for Ingestion Decorator Module.

This module contains unit tests for the cascade.ingestion.decorator module.
Tests cover decorator application, schema auto-generation, asset registration,
configuration parameters, and error handling.
"""

from datetime import datetime

import pytest
from pandera.pandas import DataFrameModel, Field
from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType

from cascade.ingestion.decorator import _INGESTION_ASSETS, cascade_ingestion, get_ingestion_assets


def get_asset_spec(asset_def):
    """Helper to get AssetSpec from AssetsDefinition."""
    key = list(asset_def.keys)[0]
    return asset_def.specs_by_key[key]


class TestSchemaAutoGeneration:
    """Test automatic PyIceberg schema generation from Pandera."""

    def test_schema_auto_generated_from_pandera(self):
        """Test PyIceberg schema is auto-generated when only validation_schema provided."""

        class TestPanderaSchema(DataFrameModel):
            id: str = Field(nullable=False)
            value: int

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestPanderaSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Verify asset was created
        assert test_asset is not None
        assert test_asset.op.name == "dlt_test_table"

    def test_explicit_iceberg_schema_used(self):
        """Test explicit PyIceberg schema is used when provided."""

        class TestPanderaSchema(DataFrameModel):
            id: str

        explicit_schema = Schema(
            NestedField(field_id=1, name="custom_field", field_type=StringType(), required=True)
        )

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestPanderaSchema,
            iceberg_schema=explicit_schema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Asset should be created successfully
        assert test_asset is not None
        assert test_asset.op.name == "dlt_test_table"

    def test_error_when_no_schema_provided(self):
        """Test error raised when neither validation_schema nor iceberg_schema provided."""

        with pytest.raises(ValueError, match="Either 'validation_schema'.*or 'iceberg_schema'"):

            @cascade_ingestion(
                table_name="test_table",
                unique_key="id",
                group="test",
            )
            def test_asset(partition_date: str):
                pass


class TestDecoratorConfiguration:
    """Test decorator parameter configuration."""

    def test_table_name_configuration(self):
        """Test table_name parameter is properly configured."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="custom_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check asset name includes table name
        assert test_asset.op.name == "dlt_custom_table"

    def test_unique_key_configuration(self):
        """Test unique_key parameter is stored."""

        class TestSchema(DataFrameModel):
            custom_id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="custom_id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Asset should be created
        assert test_asset is not None

    def test_group_name_configuration(self):
        """Test group_name parameter is applied to asset."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="custom_group",
        )
        def test_asset(partition_date: str):
            pass

        # Check asset has correct group
        spec = get_asset_spec(test_asset)
        assert spec.group_name == "custom_group"


class TestAutomationConfiguration:
    """Test automation condition and scheduling configuration."""

    def test_cron_schedule_applied(self):
        """Test cron schedule is applied when provided."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            cron="0 */1 * * *",
        )
        def test_asset(partition_date: str):
            pass

        # Check automation condition is set
        spec = get_asset_spec(test_asset)
        assert spec.automation_condition is not None

    def test_no_cron_means_no_automation(self):
        """Test no automation condition when cron not provided."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check no automation condition
        spec = get_asset_spec(test_asset)
        assert spec.automation_condition is None


class TestFreshnessConfiguration:
    """Test freshness policy configuration."""

    def test_freshness_policy_applied(self):
        """Test freshness policy is created from hours tuple."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            freshness_hours=(1, 24),
        )
        def test_asset(partition_date: str):
            pass

        # Check freshness policy is set
        spec = get_asset_spec(test_asset)
        assert spec.freshness_policy is not None

    def test_no_freshness_when_not_provided(self):
        """Test no freshness policy when freshness_hours not provided."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check no freshness policy
        spec = get_asset_spec(test_asset)
        assert spec.freshness_policy is None


class TestRetryConfiguration:
    """Test retry policy configuration."""

    def test_default_retry_policy(self):
        """Test default retry policy configuration."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check retry policy exists
        assert test_asset.op.retry_policy is not None
        assert test_asset.op.retry_policy.max_retries == 3  # Default

    def test_custom_retry_configuration(self):
        """Test custom max_retries and retry_delay configuration."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            max_retries=5,
            retry_delay_seconds=60,
        )
        def test_asset(partition_date: str):
            pass

        # Check retry policy exists
        assert test_asset.op.retry_policy is not None
        assert test_asset.op.retry_policy.max_retries == 5
        assert test_asset.op.retry_policy.delay == 60


class TestAssetRegistration:
    """Test asset registration and discovery."""

    def test_decorated_asset_registered(self):
        """Test decorated asset is added to _INGESTION_ASSETS."""

        # Clear registry before test
        initial_count = len(_INGESTION_ASSETS)

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="registration_test",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check asset was registered
        assert len(_INGESTION_ASSETS) == initial_count + 1
        assert test_asset in _INGESTION_ASSETS

    def test_get_ingestion_assets_returns_copy(self):
        """Test get_ingestion_assets() returns a copy of registered assets."""

        assets = get_ingestion_assets()

        # Should return a list
        assert isinstance(assets, list)

        # Modifying returned list should not affect internal registry
        original_length = len(_INGESTION_ASSETS)
        assets.append(None)
        assert len(_INGESTION_ASSETS) == original_length


class TestAssetAttributes:
    """Test Dagster asset attributes."""

    def test_asset_name_format(self):
        """Test asset name follows dlt_{table_name} format."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="github_events",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check asset name
        assert test_asset.op.name == "dlt_github_events"

    def test_asset_has_description(self):
        """Test asset preserves function docstring as description."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            """Custom docstring for this asset."""
            pass

        # Check description
        spec = get_asset_spec(test_asset)
        assert "Custom docstring" in spec.description

    def test_asset_compute_kind(self):
        """Test asset has correct compute_kind."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check compute kind
        assert test_asset.op.tags["dagster/compute_kind"] == "dlt+pyiceberg"

    def test_asset_has_partitions_def(self):
        """Test asset has partitions_def configured."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
        )
        def test_asset(partition_date: str):
            pass

        # Check partitions def
        spec = get_asset_spec(test_asset)
        assert spec.partitions_def is not None


class TestComplexSchemas:
    """Test decorator with complex real-world schemas."""

    def test_github_events_like_schema(self):
        """Test decorator with GitHub events-like schema."""

        class GitHubEvents(DataFrameModel):
            id: str = Field(nullable=False, unique=True, description="Event ID")
            type: str = Field(nullable=False)
            actor: str = Field(nullable=False)
            repo: str = Field(nullable=False)
            created_at: datetime = Field(nullable=False)
            public: bool = Field(nullable=False)

        @cascade_ingestion(
            table_name="github_user_events",
            unique_key="id",
            validation_schema=GitHubEvents,
            group="github",
            cron="0 */1 * * *",
            freshness_hours=(1, 24),
        )
        def github_events(partition_date: str):
            """Ingest GitHub user events."""
            pass

        # Check asset configured correctly
        spec = get_asset_spec(github_events)
        assert github_events.op.name == "dlt_github_user_events"
        assert spec.group_name == "github"
        assert spec.automation_condition is not None
        assert spec.freshness_policy is not None

    def test_glucose_entries_like_schema(self):
        """Test decorator with Nightscout glucose-like schema."""

        class GlucoseEntries(DataFrameModel):
            _id: str = Field(nullable=False, unique=True)
            sgv: int = Field(ge=1, le=1000, nullable=False)
            date: int = Field(nullable=False)
            date_string: datetime = Field(nullable=False)
            direction: str | None = Field(nullable=True)

        @cascade_ingestion(
            table_name="glucose_entries",
            unique_key="_id",
            validation_schema=GlucoseEntries,
            group="nightscout",
            cron="0 */1 * * *",
            freshness_hours=(1, 24),
            max_runtime_seconds=600,
        )
        def glucose_entries(partition_date: str):
            """Ingest Nightscout glucose entries."""
            pass

        # Check asset configured correctly
        spec = get_asset_spec(glucose_entries)
        assert glucose_entries.op.name == "dlt_glucose_entries"
        assert spec.group_name == "nightscout"
        assert glucose_entries.op.tags["dagster/max_runtime"] == "600"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_partition_spec_optional(self):
        """Test partition_spec is optional."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            partition_spec=None,
        )
        def test_asset(partition_date: str):
            pass

        # Should create asset successfully
        assert test_asset is not None

    def test_validate_flag_optional(self):
        """Test validate flag is optional."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            validate=False,
        )
        def test_asset(partition_date: str):
            pass

        # Should create asset successfully
        assert test_asset is not None

    def test_max_runtime_configuration(self):
        """Test max_runtime_seconds is applied to op_tags."""

        class TestSchema(DataFrameModel):
            id: str

        @cascade_ingestion(
            table_name="test_table",
            unique_key="id",
            validation_schema=TestSchema,
            group="test",
            max_runtime_seconds=900,
        )
        def test_asset(partition_date: str):
            pass

        # Check op_tags
        assert test_asset.op.tags["dagster/max_runtime"] == "900"
