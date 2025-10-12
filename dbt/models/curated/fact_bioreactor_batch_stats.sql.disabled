{{ config(materialized='table') }}

with agg as (
  select
    batch_id,
    tag,
    avg(value_avg) as mean_value,
    stddev(value_avg) as sd_value,
    min(value_avg) as min_value,
    max(value_avg) as max_value
  from {{ ref('int_bioreactor_downsample_5m') }}
  group by 1,2
)
select * from agg
