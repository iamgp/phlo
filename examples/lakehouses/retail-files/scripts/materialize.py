"""Materialize the local retail files into DuckDB tables for dbt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from workflows.ingestion.retail.files import read_historical_archive, read_inventory, read_products, read_sales
from workflows.quality.retail import validate_retail


def materialize(partition_date: str, database: Path = ROOT / "retail.duckdb") -> None:
    sales = read_sales(partition_date, ROOT / "data")
    products = read_products(ROOT / "data")
    inventory = read_inventory(ROOT / "data")
    archive_path = ROOT / "data" / "historical_sales.parquet"
    archive = read_historical_archive(ROOT / "data") if archive_path.exists() else sales.iloc[0:0]
    validate_retail(sales, products, inventory)
    connection = duckdb.connect(str(database))
    try:
        connection.register("incoming_sales", sales)
        connection.register("incoming_products", products)
        connection.register("incoming_inventory", inventory)
        connection.register("historical_sales", archive)
        connection.execute("CREATE TABLE IF NOT EXISTS raw_sales AS SELECT * FROM incoming_sales WHERE false")
        connection.execute("DELETE FROM raw_sales WHERE partition_date = ?", [partition_date])
        connection.execute("INSERT INTO raw_sales SELECT * FROM incoming_sales")
        connection.execute("INSERT INTO raw_sales SELECT * FROM historical_sales WHERE NOT EXISTS (SELECT 1 FROM raw_sales r WHERE r.sale_id = historical_sales.sale_id)")
        connection.execute("CREATE OR REPLACE TABLE raw_products AS SELECT * FROM incoming_products")
        connection.execute("CREATE OR REPLACE TABLE raw_inventory AS SELECT * FROM incoming_inventory")
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--partition", required=True)
    args = parser.parse_args()
    materialize(args.partition)
    print(f"Materialized retail partition {args.partition}")
