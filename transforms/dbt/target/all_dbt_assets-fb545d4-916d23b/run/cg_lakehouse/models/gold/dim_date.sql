
        
            delete from "ducklake"."main_gold"."dim_date"
            where (
                reading_date) in (
                select (reading_date)
                from "dim_date__dbt_tmp20251016200755648325"
            );

        
    

    insert into "ducklake"."main_gold"."dim_date" ("reading_date", "day_name", "day_of_week", "week_of_year", "month", "year", "reading_count", "avg_glucose_mg_dl", "min_glucose_mg_dl", "max_glucose_mg_dl", "stddev_glucose_mg_dl", "time_in_range_pct", "time_below_range_pct", "time_above_range_pct", "estimated_a1c_pct")
    (
        select "reading_date", "day_name", "day_of_week", "week_of_year", "month", "year", "reading_count", "avg_glucose_mg_dl", "min_glucose_mg_dl", "max_glucose_mg_dl", "stddev_glucose_mg_dl", "time_in_range_pct", "time_below_range_pct", "time_above_range_pct", "estimated_a1c_pct"
        from "dim_date__dbt_tmp20251016200755648325"
    )
  