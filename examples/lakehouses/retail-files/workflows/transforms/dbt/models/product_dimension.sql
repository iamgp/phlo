select product_id, product_name, category, unit_cost
from {{ source('retail_raw', 'raw_products') }}
