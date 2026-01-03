"""Integration tests for phlo-dlt using shared infrastructure."""

from unittest.mock import patch

import pytest
from pandera.pandas import DataFrameModel

from phlo.logging import get_logger
from phlo_dlt.converter import pandera_to_iceberg
from phlo_dlt.registry import TableConfig
from phlo_iceberg.resource import IcebergResource
# from phlo_dlt.decorator import phlo_ingestion # Removed to avoid Dagster dependency in this test

pytestmark = pytest.mark.integration


class MySchema(DataFrameModel):
    id: int
    name: str


def test_phlo_ingestion_execution_real(tmp_path, iceberg_catalog):
    """
    Test executing the created asset using a REAL local Iceberg catalog (backed by MinIO/Sqlite).
    This verifies the full flow: dlt -> parquet -> pyiceberg -> minio.
    """

    # 1. Define the asset
    # 1. Define the source (Just a plain python function now!)
    def my_source(partition_date: str):
        yield {"id": 1, "name": "foo"}
        yield {"id": 2, "name": "bar"}

    # 2. Setup Resources
    # We use the real IcebergResource, but we patch the catalog getter to return our
    # test-scoped fixture catalog (which points to MinIO).

    iceberg_resource = IcebergResource()

    # 3. Patch the catalog usage
    # We must patch BOTH resource.get_catalog and tables.get_catalog because they import it separately.
    # 3. Use the new Executor directly (Orchestrator Agnostic)
    # We patch both resource and tables get_catalog as before
    # We patch both resource and tables get_catalog as before
    with (
        patch("phlo_iceberg.resource.get_catalog", return_value=iceberg_catalog),
        patch("phlo_iceberg.tables.get_catalog", return_value=iceberg_catalog),
        patch("phlo_iceberg.catalog.get_catalog", return_value=iceberg_catalog),
    ):
        # Core logic setup
        table_name = "real_integration_test"
        table_config = TableConfig(
            table_name=table_name,
            iceberg_schema=pandera_to_iceberg(MySchema),
            validation_schema=MySchema,
            unique_key="id",
            group_name="integration_test",
        )

        # Initialize the Executor
        # We pass a dummy logger or use standard logging
        logger = get_logger("test_logger")

        from phlo_dlt.executor import DltIngester

        ingester = DltIngester(
            context=None,  # Ingester handles context=None gracefully or we mock it if needed
            logger=logger,
            table_config=table_config,
            iceberg_resource=iceberg_resource,
            dlt_source_func=my_source,
            add_metadata_columns=True,
            merge_strategy="merge",
        )

        # 4. Execute Logic
        partition_key = "2025-01-02"
        result = ingester.run_ingestion(partition_key=partition_key)

        assert result.status == "success"
        assert result.rows_inserted == 2

        # 5. Verify Iceberg Table Content
        table = iceberg_catalog.load_table(table_config.full_table_name)
        df = table.scan().to_arrow().to_pylist()

        assert len(df) == 2
        # Sort by id to ensure deterministic check
        df.sort(key=lambda x: x["id"])
        assert df[0]["id"] == 1
        assert df[0]["name"] == "foo"
        assert df[1]["id"] == 2
        assert df[1]["name"] == "bar"

        # Verify metadata injection
        assert "_phlo_run_id" in df[0]
        assert df[0]["_phlo_partition_date"] == "2025-01-02"
