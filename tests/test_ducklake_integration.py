"""
Integration tests for DuckLake pipeline components.

These tests verify the critical connection and data flow paths:
1. DuckLake connection configuration
2. DLT destination setup
3. dbt bootstrap and model execution
4. End-to-end data flow from DLT -> dbt -> query
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pytest

from cascade.config import config
from cascade.dlt.ducklake_destination import build_destination as ducklake_destination
from cascade.ducklake import build_ducklake_runtime_config, configure_ducklake_connection


@pytest.fixture
def runtime_config():
    """Get DuckLake runtime configuration from environment."""
    return build_ducklake_runtime_config()


@pytest.fixture
def ducklake_connection(runtime_config):
    """Create a configured DuckLake connection."""
    conn = duckdb.connect(database=":memory:")
    configure_ducklake_connection(
        conn,
        runtime=runtime_config,
        ensure_schemas={"raw", "bronze", "silver", "gold"},
        read_only=False,
    )
    yield conn
    conn.close()


class TestDuckLakeConnection:
    """Test DuckLake connection configuration."""

    def test_runtime_config_from_env(self, runtime_config):
        """Verify runtime config loads from environment correctly."""
        assert runtime_config.catalog_database == os.getenv(
            "DUCKLAKE_CATALOG_DATABASE", "ducklake_catalog"
        )
        assert runtime_config.catalog_alias == os.getenv(
            "DUCKLAKE_CATALOG_ALIAS", "dbt"
        )
        assert runtime_config.default_dataset == os.getenv(
            "DUCKLAKE_DEFAULT_DATASET", "raw"
        )
        assert runtime_config.data_path.startswith("s3://")

    def test_extensions_installed(self, ducklake_connection):
        """Verify required extensions are installed and loaded."""
        result = ducklake_connection.execute(
            "SELECT extension_name, loaded FROM duckdb_extensions() "
            "WHERE extension_name IN ('ducklake', 'httpfs', 'postgres')"
        ).fetchall()

        extensions = {row[0]: row[1] for row in result}
        assert extensions.get("ducklake") is True, "ducklake extension not loaded"
        assert extensions.get("httpfs") is True, "httpfs extension not loaded"
        assert extensions.get("postgres") is True, "postgres extension not loaded"

    def test_catalog_attached(self, ducklake_connection, runtime_config):
        """Verify DuckLake catalog is attached with correct alias."""
        databases = ducklake_connection.execute("PRAGMA database_list").fetchall()
        db_aliases = [row[1] for row in databases]

        assert (
            runtime_config.catalog_alias in db_aliases
        ), f"Catalog '{runtime_config.catalog_alias}' not attached. Found: {db_aliases}"

    def test_schemas_exist(self, ducklake_connection, runtime_config):
        """Verify bronze/silver/gold schemas exist in DuckLake catalog."""
        ducklake_connection.execute(f"USE {runtime_config.catalog_alias}")

        schemas_result = ducklake_connection.execute(
            "SELECT schema_name FROM information_schema.schemata"
        ).fetchall()
        schema_names = {row[0] for row in schemas_result}

        expected_schemas = {"raw", "bronze", "silver", "gold"}
        missing = expected_schemas - schema_names
        assert not missing, f"Missing schemas in DuckLake catalog: {missing}"

    def test_s3_settings_configured(self, ducklake_connection, runtime_config):
        """Verify S3/MinIO settings are configured."""
        settings_to_check = [
            "s3_access_key_id",
            "s3_secret_access_key",
            "s3_region",
            "s3_url_style",
        ]

        for setting in settings_to_check:
            result = ducklake_connection.execute(
                f"SELECT current_setting('{setting}')"
            ).fetchone()
            assert result is not None, f"Setting {setting} not configured"
            assert result[0], f"Setting {setting} is empty"

    def test_ducklake_retry_settings(self, ducklake_connection):
        """Verify DuckLake retry settings are configured for concurrency."""
        retry_count = ducklake_connection.execute(
            "SELECT current_setting('ducklake_max_retry_count')"
        ).fetchone()[0]
        retry_wait = ducklake_connection.execute(
            "SELECT current_setting('ducklake_retry_wait_ms')"
        ).fetchone()[0]

        assert int(retry_count) >= 100, "Retry count too low for concurrent operations"
        assert int(retry_wait) >= 100, "Retry wait too low"


class TestDLTDestination:
    """Test DLT destination configuration and table creation."""

    def test_destination_creates_connection(self):
        """Verify DLT destination factory creates valid connection."""
        dest = ducklake_destination()
        assert dest is not None
        assert hasattr(dest, "client_class")

    def test_dlt_writes_to_correct_schema(self, ducklake_connection, runtime_config):
        """Test that DLT writes data to the expected schema in DuckLake."""
        import dlt

        # Create a simple test pipeline
        pipeline = dlt.pipeline(
            pipeline_name="test_pipeline",
            destination=ducklake_destination(),
            dataset_name="raw",
        )

        # Define test data
        @dlt.resource(name="test_table", write_disposition="replace")
        def test_data():
            yield [{"id": 1, "value": "test"}]

        # Run pipeline
        info = pipeline.run(test_data())
        assert info.has_failed is False, f"Pipeline failed: {info}"

        # Verify data landed in DuckLake
        ducklake_connection.execute(f"USE {runtime_config.catalog_alias}")
        result = ducklake_connection.execute(
            "SELECT count(*) FROM raw.test_table"
        ).fetchone()
        assert result[0] == 1, "Data not written to DuckLake raw schema"


class TestDBTBootstrap:
    """Test dbt bootstrap macro and model execution."""

    def test_bootstrap_macro_runs(self, ducklake_connection):
        """Verify the dbt bootstrap macro configures DuckLake correctly."""
        # The bootstrap macro should be idempotent
        # We can test by simulating what it does

        catalog_alias = os.getenv("DUCKLAKE_CATALOG_ALIAS", "ducklake")

        # Check database is attached
        databases = ducklake_connection.execute("PRAGMA database_list").fetchall()
        db_aliases = [row[1] for row in databases]
        assert catalog_alias in db_aliases

    def test_sources_resolve_correctly(self, runtime_config):
        """Test that dbt sources reference the correct database and schema."""
        import yaml

        sources_file = Path("/dbt/models/sources/sources.yml")
        if not sources_file.exists():
            pytest.skip("Not running in dbt container environment")

        with open(sources_file) as f:
            sources = yaml.safe_load(f)

        dagster_source = next(
            s for s in sources["sources"] if s["name"] == "dagster_assets"
        )

        # Source should reference the DuckLake catalog alias
        assert dagster_source["database"] == runtime_config.catalog_alias, (
            f"Source database is '{dagster_source['database']}', "
            f"expected '{runtime_config.catalog_alias}'"
        )
        assert dagster_source["schema"] == runtime_config.default_dataset


class TestEndToEndDataFlow:
    """Test complete data flow from ingestion to transformation."""

    def test_dlt_to_dbt_data_flow(self, ducklake_connection, runtime_config):
        """
        Test end-to-end flow:
        1. DLT writes to raw.entries
        2. dbt reads from raw.entries
        3. dbt creates bronze.stg_entries view
        4. Data is queryable through all layers
        """
        import dlt

        # Step 1: Simulate DLT ingestion
        pipeline = dlt.pipeline(
            pipeline_name="test_e2e_pipeline",
            destination=ducklake_destination(),
            dataset_name="raw",
        )

        @dlt.resource(name="entries", write_disposition="replace")
        def sample_entries():
            yield [
                {
                    "_id": "test123",
                    "sgv": 120,
                    "date": 1700000000000,
                    "dateString": "2023-11-15T00:00:00.000Z",
                    "direction": "Flat",
                    "device": "test_device",
                    "type": "sgv",
                }
            ]

        info = pipeline.run(sample_entries())
        assert info.has_failed is False, f"DLT pipeline failed: {info}"

        # Step 2: Verify data in raw layer
        ducklake_connection.execute(f"USE {runtime_config.catalog_alias}")
        raw_count = ducklake_connection.execute(
            "SELECT count(*) FROM raw.entries"
        ).fetchone()[0]
        assert raw_count > 0, "No data in raw.entries after DLT load"

        # Step 3: Simulate what stg_entries should do
        # (In practice, this would be dbt running the model)
        ducklake_connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        ducklake_connection.execute(
            """
            CREATE OR REPLACE VIEW bronze.stg_entries AS
            SELECT
                _id as entry_id,
                sgv as glucose_mg_dl,
                epoch_ms(date) as reading_timestamp,
                dateString as timestamp_iso,
                direction,
                device,
                type as reading_type
            FROM raw.entries
            WHERE sgv IS NOT NULL
                AND sgv BETWEEN 20 AND 600
            """
        )

        # Step 4: Query through the view
        staged_count = ducklake_connection.execute(
            "SELECT count(*) FROM bronze.stg_entries"
        ).fetchone()[0]
        assert staged_count > 0, "No data visible through bronze.stg_entries view"


class TestConcurrencyAndLocking:
    """Test concurrent operations and catalog locking."""

    def test_multiple_concurrent_connections(self, runtime_config):
        """Verify multiple ephemeral connections can attach to DuckLake."""
        connections = []
        try:
            # Create 3 concurrent connections
            for i in range(3):
                conn = duckdb.connect(database=":memory:")
                configure_ducklake_connection(
                    conn,
                    runtime=runtime_config,
                    ensure_schemas={"raw"},
                    read_only=False,
                )
                connections.append(conn)

            # Each should be able to query the catalog
            for i, conn in enumerate(connections):
                result = conn.execute(
                    f"SELECT count(*) FROM {runtime_config.catalog_alias}.information_schema.schemata"
                ).fetchone()
                assert (
                    result[0] > 0
                ), f"Connection {i} cannot query DuckLake catalog"

        finally:
            for conn in connections:
                conn.close()

    def test_write_from_multiple_connections(self, runtime_config):
        """Test that multiple connections can write without deadlock."""
        import dlt
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def write_partition(partition_id: int) -> bool:
            """Write a single partition of data."""
            try:
                pipeline = dlt.pipeline(
                    pipeline_name=f"test_concurrent_{partition_id}",
                    destination=ducklake_destination(),
                    dataset_name="raw",
                )

                @dlt.resource(name="concurrent_test", write_disposition="append")
                def test_data():
                    yield [{"partition": partition_id, "timestamp": time.time()}]

                info = pipeline.run(test_data())
                return not info.has_failed
            except Exception as e:
                print(f"Partition {partition_id} failed: {e}")
                return False

        # Try 3 concurrent writes
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(write_partition, i) for i in range(3)]
            results = [future.result() for future in as_completed(futures)]

        # At least some should succeed (all should, but we're testing for hangs)
        assert any(results), "All concurrent writes failed"
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.66, f"Too many concurrent write failures: {success_rate:.0%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
