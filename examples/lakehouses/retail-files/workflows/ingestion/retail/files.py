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
    expected = [(day.name, store.store_id) for day in sorted((data / "sales").iterdir()) for store in stores.itertuples()]
    missing = [f"{day}/{store}.csv" for day, store in expected if not (data / "sales" / day / f"{store}.csv").exists()]
    if missing: raise FileNotFoundError(f"Missing required store files: {missing[:5]}")
    return pd.concat([pd.read_csv(data / "sales" / day / f"{store}.csv") for day, store in expected], ignore_index=True)
def read_inventory(data: Path) -> pd.DataFrame: return pd.read_json(data / "inventory.ndjson", lines=True, convert_dates=False)
def read_historical_archive(data: Path) -> pd.DataFrame: return pd.read_parquet(data / "historical_sales.parquet")

@phlo.ingestion(table_name="retail_sales_lines", unique_key="line_id", validation_schema=SalesSchema, group="retail")
def retail_sales_lines(partition_date: str) -> object:
    return dlt.resource(read_sales(Path("generated-data")).query("partition_date == @partition_date").to_dict("records"), name="retail_sales_lines")
@phlo.ingestion(table_name="retail_products", unique_key="product_id", validation_schema=ProductsSchema, group="retail")
def retail_products(partition_date: str) -> object:
    del partition_date; return dlt.resource(read_reference(Path("generated-data"), "products").to_dict("records"), name="retail_products")
@phlo.ingestion(table_name="retail_inventory", unique_key="product_id", validation_schema=InventorySchema, group="retail")
def retail_inventory(partition_date: str) -> object:
    return dlt.resource(read_inventory(Path("generated-data")).query("partition_date == @partition_date").to_dict("records"), name="retail_inventory")
