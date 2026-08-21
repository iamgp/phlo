"""Generate the deterministic Parquet archive and optional failure paths."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def generate() -> Path:
    archive = pd.DataFrame(
        [{"sale_id": "S-099", "store_id": "store-1", "product_id": "SKU-1", "sold_at": "2025-01-14T16:00:00Z", "quantity": 1, "unit_price": 10.0, "partition_date": "2025-01-14", "revenue": 10.0}]
    )
    path = DATA / "historical_sales.parquet"
    archive.to_parquet(path, index=False)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--missing-store", metavar="DATE")
    args = parser.parse_args()
    if args.missing_store:
        missing = DATA / f"sales_{args.missing_store}.csv"
        missing.unlink(missing_ok=True)
        print(f"Removed {missing}")
    else:
        print(generate())
