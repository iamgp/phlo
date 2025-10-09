# Superset Glucose Dashboard Setup

This guide walks through wiring Apache Superset to the published mart tables in Postgres
and rebuilding the “Continuous Glucose Monitoring Dashboard” manually.

## 1. Prerequisites
- Build the Superset image so the Postgres driver is present:
  ```
  docker compose build superset
  docker compose up -d superset
  ```
- All services running with `docker compose up -d` (Airbyte, Dagster, Postgres, Superset, etc.).
- Dagster pipeline has run `publish_glucose_marts_to_postgres` at least once so the
  Postgres schema `marts` contains the latest tables.
- Superset available at `http://localhost:8088` with the default admin credentials
  (`admin` / `admin123`, unless overridden in `.env`).

## 2. Register the Postgres data source
1. Sign in to Superset.
2. Go to **Settings → Database Connections → + Database**.
3. Choose **PostgreSQL**.
4. Set **Display Name** to `Lakehouse Postgres`.
5. In **SQLAlchemy URI** enter:
   ```
   postgresql+psycopg2://lake:lakepass@postgres:5432/lakehouse
   ```
   (Adjust for custom credentials or ports from `.env`.)
6. Click **Test Connection**. If it succeeds, click **Connect** / **Finish**.

## 3. Create datasets for the marts
For each mart table that the dashboard needs:
1. Navigate to **Data → Datasets → + Dataset**.
2. Pick the **Lakehouse Postgres** database.
3. Under **Schema**, choose `marts`.
4. Select the table and save:
   - `mart_glucose_overview`
   - `mart_glucose_hourly_patterns`
   - `fact_glucose_readings`
5. After each dataset is saved, open it once and click **Sync Columns** so Superset
   retrieves the latest field definitions.

## 4. Recreate the charts
Superset saves charts separately from the dashboard. Build the following five visuals.

### 4.1 Current Glucose Level
- Dataset: `mart_glucose_overview`
- Visualization: **Big Number**
- Metric: `AVG(glucose_mg_dl)` (or select the existing `avg_glucose_mg_dl` column as the metric)
- Sort: `reading_date` descending; limit 1 record
- Customize label: “Current Glucose Level”

### 4.2 Time in Range (Today)
- Dataset: `mart_glucose_overview`
- Visualization: **Big Number**
- Metric: `AVG(time_in_range_pct)`
- Add a time filter `reading_date == today`
- Label: “Time in Range (Today)”

### 4.3 Glucose Trend (7 Days)
- Dataset: `mart_glucose_overview`
- Visualization: **Line Chart**
- Metrics: `avg_glucose_mg_dl` as the primary line; add `min_glucose_mg_dl` and
  `max_glucose_mg_dl` as additional series or tooltips if desired.
- Time range: “Last 7 days”
- Time grain: `day`
- Format x-axis as `%b %d`; y-axis bounds `0 – 400`
- Title: “Glucose Trend (7 Days)”

### 4.4 Glucose Patterns by Time of Day
- Dataset: `mart_glucose_hourly_patterns`
- Visualization: **Heatmap**
- X Axis: `hour_of_day`
- Y Axis: `day_name`
- Metric: `avg_glucose_mg_dl`
- Adjust color scheme to “Blue White Yellow” for clarity.
- Title: “Glucose Patterns by Time of Day”

### 4.5 Time Distribution
- Dataset: `mart_glucose_overview`
- Visualization: **Pie / Donut Chart**
- Group by: `glucose_category`
- Metric: `SUM(reading_count)` (or use percentage columns for hover tooltips)
- Enable donut mode and outside labels.
- Time range: “Last 7 days”
- Title: “Time Distribution”

## 5. Assemble the dashboard
1. Go to **Dashboards → + Dashboard** and name it “Continuous Glucose Monitoring Dashboard”.
2. Edit the dashboard and add each saved chart.
3. Arrange tiles to match the intended layout:
   - Top row: the two big number charts side by side.
   - Middle: the 7-day line chart spanning the full width.
   - Bottom: heatmap (left) and donut (right).
4. Optional: set an automatic refresh interval (e.g., every 5 minutes) via the
   dashboard settings.
5. Save the dashboard.

## 6. Keeping data fresh
- The DuckDB marts remain the source of truth. After dbt finishes building them,
  run the Dagster asset `publish_glucose_marts_to_postgres` to push fresh data to Postgres:
  ```
  docker exec dagster-web dagster asset materialize --select publish_glucose_marts_to_postgres -f /opt/dagster/repository.py
  ```
  (Or trigger it from the Dagster UI.)
- Once the Postgres tables are updated, refresh the Superset dashboard to see the new metrics.

With these steps, Superset reads the published `marts` tables reliably, and the dashboard
mirrors the JSON design without relying on direct database manipulation.
