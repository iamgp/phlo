select store_id, product_id, observed_at, on_hand, reserved, in_transit, reorder_point, safety_stock,
       on_hand - reserved as available_to_sell, partition_date
from {{ source('retail_raw', 'raw_inventory') }}
