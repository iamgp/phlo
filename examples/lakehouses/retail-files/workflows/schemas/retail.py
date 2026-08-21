from __future__ import annotations

import pandera.pandas as pa
from pandera.typing import Series


class SalesSchema(pa.DataFrameModel):
    sale_id: Series[str] = pa.Field(unique=True)
    store_id: Series[str]
    product_id: Series[str]
    sold_at: Series[str]
    quantity: Series[int] = pa.Field(gt=0)
    unit_price: Series[float] = pa.Field(ge=0)
    partition_date: Series[str]
    revenue: Series[float] = pa.Field(ge=0)


class ProductsSchema(pa.DataFrameModel):
    product_id: Series[str] = pa.Field(unique=True)
    product_name: Series[str]
    category: Series[str]
    unit_cost: Series[float] = pa.Field(ge=0)


class InventorySchema(pa.DataFrameModel):
    store_id: Series[str]
    product_id: Series[str]
    observed_at: Series[str]
    on_hand: Series[int] = pa.Field(ge=0)
