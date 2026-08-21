import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_fixtures import generate
from workflows.ingestion.retail.files import read_inventory, read_reference, read_sales
from workflows.quality.retail import validate_retail


def fixture(tmp_path):
    data = tmp_path / "data"
    generate(data, "test")
    return data


def test_test_scale_and_completeness(tmp_path):
    data = fixture(tmp_path)
    sales = read_sales(data)
    assert len(sales) == 160 and len(list((data / "sales").rglob("*.csv"))) == 4
    (data / "sales" / "2025-01-01" / "S001.csv").unlink()
    with pytest.raises(FileNotFoundError, match="store files"):
        read_sales(data)


def test_quality_failure_cases(tmp_path):
    data = fixture(tmp_path)
    sales = read_sales(data)
    products = read_reference(data, "products")
    stores = read_reference(data, "stores")
    promos = read_reference(data, "promotions")
    inventory = read_inventory(data)
    validate_retail(sales, products, stores, promos, inventory)
    for name in ["duplicate_line.csv", "unknown_product.csv", "bad_arithmetic.csv"]:
        with pytest.raises(Exception):
            validate_retail(
                pd.read_csv(data / "failures" / name), products, stores, promos, inventory
            )


def test_parquet_and_ndjson_are_used(tmp_path):
    data = fixture(tmp_path)
    assert (data / "historical_sales.parquet").stat().st_size > 0
    assert len(read_inventory(data)) == 40
