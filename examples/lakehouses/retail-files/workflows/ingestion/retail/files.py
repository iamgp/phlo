from __future__ import annotations

import json
from pathlib import Path

import dlt
import pandas as pd

import phlo
from workflows.schemas.retail import InventorySchema, ProductsSchema, SalesSchema


def read_reference(data: Path, name: str) -> pd.DataFrame:
    return pd.DataFrame(json.loads((data / f"{name}.json").read_text(encoding="utf-8")))


def read_sales(data: Path) -> pd.DataFrame:
    stores = read_reference(data, "stores")
    expected = [
        (day.name, store.store_id)
        for day in sorted((data / "sales").iterdir())
        for store in stores.itertuples()
    ]
    missing = [
        f"{day}/{store}.csv"
        for day, store in expected
        if not (data / "sales" / day / f"{store}.csv").exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing required store files: {missing[:5]}")
    return pd.concat(
        [pd.read_csv(data / "sales" / day / f"{store}.csv") for day, store in expected],
        ignore_index=True,
    )


def read_inventory(data: Path) -> pd.DataFrame:
    return pd.read_json(data / "inventory.ndjson", lines=True, convert_dates=False)


def read_historical_archive(data: Path) -> pd.DataFrame:
    return pd.read_parquet(data / "historical_sales.parquet")


@phlo.ingest.dlt(
    table_name="retail_sales_lines",
    unique_key="line_id",
    validation_schema=SalesSchema,
    group="retail",
    cron="15 2 * * *",
    freshness_hours=(24, 30),
    merge_strategy="merge",
    strict_validation=True,
    max_runtime_seconds=1800,
    max_retries=3,
    retry_delay_seconds=60,
    add_metadata_columns=True,
    owner="retail-finance",
    consumers=["finance", "analytics"],
)
def retail_sales_lines(partition_date: str) -> object:
    return dlt.resource(
        read_sales(Path("generated-data"))
        .query("partition_date == @partition_date")
        .to_dict("records"),
        name="retail_sales_lines",
    )


@phlo.ingest.dlt(
    table_name="retail_products",
    unique_key="product_id",
    validation_schema=ProductsSchema,
    group="retail",
    cron="0 3 * * *",
    freshness_hours=(72, 96),
    merge_strategy="merge",
    strict_validation=True,
    max_runtime_seconds=300,
    max_retries=1,
    retry_delay_seconds=30,
    add_metadata_columns=True,
    owner="retail-master-data",
)
def retail_products(partition_date: str) -> object:
    del partition_date
    return dlt.resource(
        read_reference(Path("generated-data"), "products").to_dict("records"),
        name="retail_products",
    )


@phlo.ingest.dlt(
    table_name="retail_inventory",
    unique_key="inventory_snapshot_id",
    validation_schema=InventorySchema,
    group="retail",
    cron="0 * * * *",
    freshness_hours=(2, 4),
    merge_strategy="append",
    strict_validation=True,
    max_runtime_seconds=900,
    max_retries=5,
    retry_delay_seconds=30,
    add_metadata_columns=True,
    owner="retail-operations",
    consumers=["operations"],
)
def retail_inventory(partition_date: str) -> object:
    return dlt.resource(
        read_inventory(Path("generated-data"))
        .query("partition_date == @partition_date")
        .to_dict("records"),
        name="retail_inventory",
    )
