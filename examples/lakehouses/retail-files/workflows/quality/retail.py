"""Business checks intentionally executable without a running service stack."""

from __future__ import annotations

import pandas as pd

from workflows.schemas.retail import InventorySchema, ProductsSchema, SalesSchema


def validate_retail(sales: pd.DataFrame, products: pd.DataFrame, inventory: pd.DataFrame) -> None:
    SalesSchema.validate(sales)
    ProductsSchema.validate(products)
    InventorySchema.validate(inventory)
    duplicates = sales[sales.duplicated("sale_id", keep=False)]
    if not duplicates.empty:
        raise ValueError(f"Duplicate sale_id values: {sorted(duplicates.sale_id.unique())}")
    missing_products = sorted(set(sales.product_id) - set(products.product_id))
    if missing_products:
        raise ValueError(f"Sales reference unknown products: {missing_products}")
    expected_revenue = (sales.quantity * sales.unit_price).sum()
    if round(float(sales.revenue.sum()), 2) != round(float(expected_revenue), 2):
        raise ValueError("Revenue reconciliation failed")
