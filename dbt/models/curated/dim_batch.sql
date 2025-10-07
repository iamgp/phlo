{{ config(materialized='table') }}
-- Seed or reference table could supply batch metadata
select distinct batch_id, site
from {{ ref('stg_bioreactor') }};
