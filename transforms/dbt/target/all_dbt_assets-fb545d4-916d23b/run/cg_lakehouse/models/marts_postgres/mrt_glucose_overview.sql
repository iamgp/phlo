
        
            delete from "ducklake"."main_marts"."mrt_glucose_overview"
            where (
                reading_date) in (
                select (reading_date)
                from "mrt_glucose_overview__dbt_tmp20251016200755754238"
            );

        
    

    insert into "ducklake"."main_marts"."mrt_glucose_overview" ("reading_date", "day_name", "week_of_year", "month", "year", "reading_count", "avg_glucose_mg_dl", "min_glucose_mg_dl", "max_glucose_mg_dl", "stddev_glucose_mg_dl", "time_in_range_pct", "time_below_range_pct", "time_above_range_pct", "estimated_a1c_pct", "estimated_a1c_7d_avg", "glucose_change_from_prev_day", "coefficient_of_variation")
    (
        select "reading_date", "day_name", "week_of_year", "month", "year", "reading_count", "avg_glucose_mg_dl", "min_glucose_mg_dl", "max_glucose_mg_dl", "stddev_glucose_mg_dl", "time_in_range_pct", "time_below_range_pct", "time_above_range_pct", "estimated_a1c_pct", "estimated_a1c_7d_avg", "glucose_change_from_prev_day", "coefficient_of_variation"
        from "mrt_glucose_overview__dbt_tmp20251016200755754238"
    )
  