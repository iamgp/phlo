{{ config(materialized='table') }}

with base as (
  select * from {{ ref('stg_bioreactor') }}
),
bucketed as (
  select
    batch_id,
    equipment_id,
    date_trunc('minute', ts) - (extract(minute from ts)::int % 5) * interval '1 minute' as ts_5m,
    tag,
    avg(value) as value_avg
  from base
  group by 1,2,3,4
)
select * from bucketed;
