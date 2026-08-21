from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generate_fixtures import generate
from scripts.materialize import materialize
from workflows.ingestion.retail.files import read_inventory, read_sales
from workflows.quality.retail import validate_retail


def test_materialize_is_partition_idempotent(tmp_path: Path) -> None:
    generate()
    database = tmp_path / "retail.duckdb"
    materialize("2025-01-15", database)
    materialize("2025-01-15", database)
    connection = duckdb.connect(str(database))
    try:
        assert connection.sql("select count(*) from raw_sales").fetchone() == (3,)
        assert connection.sql("select sum(revenue) from raw_sales where partition_date = '2025-01-15'").fetchone() == (47.0,)
    finally:
        connection.close()


def test_duplicate_sale_is_rejected() -> None:
    sales = pd.read_csv(ROOT / "data/failures/sales_duplicate.csv")
    sales["partition_date"] = "2025-01-15"
    sales["revenue"] = sales.quantity * sales.unit_price
    with pytest.raises(Exception, match="sale_id|Duplicate"):
        validate_retail(
            sales,
            pd.read_json(ROOT / "data/products.json"),
            read_inventory(ROOT / "data"),
        )


def test_missing_store_file_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Missing required store sales file"):
        read_sales("2025-01-16", tmp_path)


def test_malformed_failure_fixtures_are_not_normal_inputs() -> None:
    with pytest.raises(ValueError):
        pd.read_json(ROOT / "data/failures/products_malformed.json")
    with pytest.raises(ValueError):
        pd.read_json(ROOT / "data/failures/inventory_malformed.ndjson", lines=True)
