select
    sale_id,
    store_id,
    product_id,
    cast(sold_at as timestamp) as sold_at,
    quantity,
    unit_price,
    revenue,
    partition_date
from {{ source('retail_raw', 'raw_sales') }}
