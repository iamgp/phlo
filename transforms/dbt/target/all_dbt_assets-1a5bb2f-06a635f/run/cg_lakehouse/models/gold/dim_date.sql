
  
    
    

    create  table
      "memory"."main_gold"."dim_date"
  
    as (
      

/*
Date dimension for glucose analytics

Provides a daily grain view with key metrics aggregated by day.
Useful for trend analysis and long-term glucose management tracking.
*/

select
    reading_date,
    dayname(reading_date) as day_name,
    extract(dow from reading_date) as day_of_week,
    extract(week from reading_date) as week_of_year,
    extract(month from reading_date) as month,
    extract(year from reading_date) as year,

    -- Daily statistics
    count(*) as reading_count,
    round(avg(glucose_mg_dl), 1) as avg_glucose_mg_dl,
    min(glucose_mg_dl) as min_glucose_mg_dl,
    max(glucose_mg_dl) as max_glucose_mg_dl,
    round(stddev(glucose_mg_dl), 1) as stddev_glucose_mg_dl,

    -- Time in range metrics (standard: 70-180 mg/dL)
    round(100.0 * sum(is_in_range) / count(*), 1) as time_in_range_pct,
    round(100.0 * sum(case when glucose_mg_dl < 70 then 1 else 0 end) / count(*), 1) as time_below_range_pct,
    round(100.0 * sum(case when glucose_mg_dl > 180 then 1 else 0 end) / count(*), 1) as time_above_range_pct,

    -- Glucose management indicator (GMI) approximation
    -- GMI = 3.31 + 0.02392 * avg_glucose_mg_dl
    round(3.31 + (0.02392 * avg(glucose_mg_dl)), 2) as estimated_a1c_pct

from "memory"."main_silver"."fct_glucose_readings"



group by reading_date
order by reading_date desc
    );
  
  
  