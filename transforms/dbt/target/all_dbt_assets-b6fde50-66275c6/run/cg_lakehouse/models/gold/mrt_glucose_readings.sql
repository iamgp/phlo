
        
            delete from "dbt"."main_gold"."mrt_glucose_readings"
            where (
                entry_id) in (
                select (entry_id)
                from "mrt_glucose_readings__dbt_tmp20251016012700644921"
            );

        
    

    insert into "dbt"."main_gold"."mrt_glucose_readings" ("entry_id", "glucose_mg_dl", "reading_timestamp", "reading_date", "hour_of_day", "day_of_week", "day_name", "glucose_category", "is_in_range", "glucose_change_mg_dl", "direction", "trend", "device")
    (
        select "entry_id", "glucose_mg_dl", "reading_timestamp", "reading_date", "hour_of_day", "day_of_week", "day_name", "glucose_category", "is_in_range", "glucose_change_mg_dl", "direction", "trend", "device"
        from "mrt_glucose_readings__dbt_tmp20251016012700644921"
    )
  