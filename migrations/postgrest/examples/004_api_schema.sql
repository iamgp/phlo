-- Migration: 004_api_schema.sql
-- Create API schema with views exposing marts data

-- Create api schema (exposed via PostgREST)
CREATE SCHEMA IF NOT EXISTS api;

-- View: Glucose Readings (from mrt_glucose_overview)
CREATE OR REPLACE VIEW api.glucose_readings AS
SELECT
  reading_date,
  day_name,
  week_of_year,
  month,
  year,
  reading_count,
  avg_glucose_mg_dl,
  min_glucose_mg_dl,
  max_glucose_mg_dl,
  time_in_range_pct,
  time_below_range_pct,
  time_above_range_pct,
  estimated_a1c_pct,
  coefficient_of_variation
FROM marts.mrt_glucose_overview
ORDER BY reading_date DESC;

-- View: Daily Summary (focused subset for dashboards)
CREATE OR REPLACE VIEW api.glucose_daily_summary AS
SELECT
  reading_date,
  day_name,
  week_of_year,
  month,
  year,
  reading_count,
  avg_glucose_mg_dl,
  time_in_range_pct,
  estimated_a1c_pct,
  estimated_a1c_7d_avg
FROM marts.mrt_glucose_overview
ORDER BY reading_date DESC;

-- View: Hourly Patterns
CREATE OR REPLACE VIEW api.glucose_hourly_patterns AS
SELECT
  hour_of_day,
  day_of_week,
  day_name,
  reading_count,
  avg_glucose_mg_dl,
  median_glucose_mg_dl,
  p25_glucose_mg_dl,
  p75_glucose_mg_dl,
  time_in_range_pct,
  stddev_glucose_mg_dl
FROM marts.mrt_glucose_hourly_patterns
ORDER BY day_of_week, hour_of_day;

-- Grant usage on api schema
GRANT USAGE ON SCHEMA api TO postgres;

-- Comments for documentation
COMMENT ON SCHEMA api IS 'API schema exposed via PostgREST';
COMMENT ON VIEW api.glucose_readings IS 'All glucose readings with daily aggregations';
COMMENT ON VIEW api.glucose_daily_summary IS 'Daily glucose summary for dashboards';
COMMENT ON VIEW api.glucose_hourly_patterns IS 'Hourly patterns across all data';
