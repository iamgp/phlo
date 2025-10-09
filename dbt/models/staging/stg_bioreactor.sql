{{ config(materialized='view') }}

{% set upstream = source('dagster_assets', 'raw_bioreactor_data') %}

-- External table over Parquet in /raw (mounted or s3://lake/raw/)
select
  cast(batch_id as varchar) as batch_id,
  equipment_id,
  ts::timestamp as ts,
  cast(tag as varchar) as tag,
  cast(value as double) as value,
  site
from read_parquet('/data/lake/raw/bioreactor/*.parquet')
