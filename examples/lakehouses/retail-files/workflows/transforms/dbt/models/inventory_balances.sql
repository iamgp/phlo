select store_id, product_id, observed_at, on_hand
from {{ source('retail_raw', 'raw_inventory') }}
