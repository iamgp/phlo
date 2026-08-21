select
    partition_date as sales_date,
    store_id,
    count(*) as sale_count,
    sum(revenue) as revenue
from {{ ref('sales_facts') }}
group by 1, 2
