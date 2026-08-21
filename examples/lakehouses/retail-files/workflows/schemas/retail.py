from __future__ import annotations
import pandera.pandas as pa
from pandera.typing import Series

class SalesSchema(pa.DataFrameModel):
    transaction_id: Series[str]; line_id: Series[str]; store_id: Series[str]; register_id: Series[str]; cashier_id: Series[str]; customer_id: Series[str]; product_id: Series[str]; sold_at: Series[str]
    quantity: Series[int]; list_price: Series[float]; unit_price: Series[float]; gross_amount: Series[float]; discount_amount: Series[float]; tax_amount: Series[float]; net_amount: Series[float]; currency: Series[str]; payment_method: Series[str]; channel: Series[str]; promotion_id: Series[str] | None = pa.Field(nullable=True); is_return: Series[bool]; partition_date: Series[str]
class ProductsSchema(pa.DataFrameModel):
    product_id: Series[str] = pa.Field(unique=True); product_name: Series[str]; category: Series[str]; subcategory: Series[str]; brand: Series[str]; supplier_id: Series[str]; unit_cost: Series[float]; list_price: Series[float]; active: Series[bool]; created_at: Series[str]; updated_at: Series[str]
class InventorySchema(pa.DataFrameModel):
    store_id: Series[str]; product_id: Series[str]; observed_at: Series[str]; on_hand: Series[int] = pa.Field(ge=0); reserved: Series[int] = pa.Field(ge=0); in_transit: Series[int] = pa.Field(ge=0); reorder_point: Series[int] = pa.Field(ge=0); safety_stock: Series[int] = pa.Field(ge=0); partition_date: Series[str]
