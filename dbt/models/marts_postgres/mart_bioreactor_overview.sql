{{ config(target='postgres', materialized='table') }}

select
  d.batch_id,
  d.site,
  s.tag,
  s.mean_value,
  s.sd_value,
  s.min_value,
  s.max_value
from {{ ref('dim_batch') }} d
join {{ ref('fact_bioreactor_batch_stats') }} s
  on d.batch_id = s.batch_id;
