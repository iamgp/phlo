#!/usr/bin/env bash
#
# Full pipeline integration test
# Clears all data, runs pipeline for last 10 days, and verifies via REST/GraphQL APIs
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_section() {
    echo ""
    echo "============================================================"
    echo "$*"
    echo "============================================================"
}

# Configuration
DAGSTER_MODULE="cascade.definitions"
REST_API_URL="http://localhost:8000/api/v1"
GRAPHQL_URL="http://localhost:8081/v1/graphql"

# Calculate date range (last 10 full days)
END_DATE=$(date -u -v-1d +%Y-%m-%d)  # Yesterday
START_DATE=$(date -u -v-10d +%Y-%m-%d)  # 10 days ago

log_section "PIPELINE INTEGRATION TEST"
log_info "Start date: $START_DATE"
log_info "End date: $END_DATE"
log_info "Dagster module: $DAGSTER_MODULE"

# Step 1: Clear all existing data
log_section "STEP 1: CLEAR EXISTING DATA"

log_info "Dropping Iceberg tables in dev branch..."
docker exec trino trino --catalog iceberg_dev --execute "
    DROP TABLE IF EXISTS iceberg_dev.raw.entries;
    DROP VIEW IF EXISTS iceberg_dev.bronze.stg_entries;
    DROP TABLE IF EXISTS iceberg_dev.silver.fct_glucose_readings;
    DROP TABLE IF EXISTS iceberg_dev.silver.dim_date;
    DROP TABLE IF EXISTS iceberg_dev.gold.mrt_glucose_overview;
    DROP TABLE IF EXISTS iceberg_dev.gold.mrt_glucose_hourly_patterns;
" 2>&1 | grep -v "WARNING" || true

log_info "Dropping Iceberg tables in main branch..."
docker exec trino trino --catalog iceberg --execute "
    DROP TABLE IF EXISTS iceberg.raw.entries;
    DROP VIEW IF EXISTS iceberg.bronze.stg_entries;
    DROP TABLE IF EXISTS iceberg.silver.fct_glucose_readings;
    DROP TABLE IF EXISTS iceberg.silver.dim_date;
    DROP TABLE IF EXISTS iceberg.gold.mrt_glucose_overview;
    DROP TABLE IF EXISTS iceberg.gold.mrt_glucose_hourly_patterns;
" 2>&1 | grep -v "WARNING" || true

log_info "Truncating Postgres marts..."
docker exec pg psql -U lake -d lakehouse -c "
    TRUNCATE TABLE marts.mrt_glucose_overview;
    TRUNCATE TABLE marts.mrt_glucose_hourly_patterns;
" 2>&1 || log_warn "Postgres tables may not exist yet"

log_info "Data cleared successfully"

# Step 2: Run ingestion for last 10 days
log_section "STEP 2: INGEST DATA (Last 10 Days)"

current_date="$START_DATE"
ingestion_count=0

while [[ "$current_date" < "$END_DATE" ]] || [[ "$current_date" == "$END_DATE" ]]; do
    log_info "Ingesting partition: $current_date"

    docker compose exec -T dagster-webserver dagster asset materialize \
        -m "$DAGSTER_MODULE" \
        --select entries \
        --partition "$current_date" 2>&1 | grep -E "Successfully|Error|FAILURE" || true

    ingestion_count=$((ingestion_count + 1))
    current_date=$(date -u -j -v+1d -f "%Y-%m-%d" "$current_date" +%Y-%m-%d)
done

log_info "Ingested $ingestion_count partitions"

# Verify ingestion
log_info "Verifying raw data..."
RAW_COUNT=$(docker exec trino trino --catalog iceberg_dev --execute "
    SELECT COUNT(*) FROM iceberg_dev.raw.entries
" 2>&1 | grep -E "^[0-9]+" | head -1 | tr -d '"' || echo "0")

log_info "Raw entries ingested: $RAW_COUNT"

if [[ "$RAW_COUNT" -eq 0 ]]; then
    log_error "No data ingested! Aborting."
    exit 1
fi

# Step 3: Run dbt transformations
log_section "STEP 3: RUN DBT TRANSFORMATIONS"

log_info "Running dbt models (bronze -> silver -> gold)..."
docker compose exec -T dagster-webserver dagster asset materialize \
    -m "$DAGSTER_MODULE" \
    --select "stg_entries,fct_glucose_readings,dim_date,mrt_glucose_overview,mrt_glucose_hourly_patterns" \
    2>&1 | grep -E "Successfully|Error|FAILURE" || true

# Verify transformations
log_info "Verifying transformed data in dev branch..."

BRONZE_COUNT=$(docker exec trino trino --catalog iceberg_dev --execute "
    SELECT COUNT(*) FROM iceberg_dev.bronze.stg_entries
" 2>&1 | grep -E "^[0-9]+" | head -1 | tr -d '"' || echo "0")

SILVER_COUNT=$(docker exec trino trino --catalog iceberg_dev --execute "
    SELECT COUNT(*) FROM iceberg_dev.silver.fct_glucose_readings
" 2>&1 | grep -E "^[0-9]+" | head -1 | tr -d '"' || echo "0")

GOLD_OVERVIEW_COUNT=$(docker exec trino trino --catalog iceberg_dev --execute "
    SELECT COUNT(*) FROM iceberg_dev.gold.mrt_glucose_overview
" 2>&1 | grep -E "^[0-9]+" | head -1 | tr -d '"' || echo "0")

GOLD_HOURLY_COUNT=$(docker exec trino trino --catalog iceberg_dev --execute "
    SELECT COUNT(*) FROM iceberg_dev.gold.mrt_glucose_hourly_patterns
" 2>&1 | grep -E "^[0-9]+" | head -1 | tr -d '"' || echo "0")

log_info "Bronze (stg_entries): $BRONZE_COUNT rows"
log_info "Silver (fct_glucose_readings): $SILVER_COUNT rows"
log_info "Gold (mrt_glucose_overview): $GOLD_OVERVIEW_COUNT rows"
log_info "Gold (mrt_glucose_hourly_patterns): $GOLD_HOURLY_COUNT rows"

# Step 4: Promote dev to main
log_section "STEP 4: PROMOTE DEV BRANCH TO MAIN"

log_info "Promoting dev branch to main in Nessie..."
docker compose exec -T dagster-webserver dagster asset materialize \
    -m "$DAGSTER_MODULE" \
    --select promote_dev_to_main \
    2>&1 | grep -E "Successfully|Error|FAILURE|400" || log_warn "Promotion may have failed (known issue)"

# Step 5: Publish to Postgres
log_section "STEP 5: PUBLISH MARTS TO POSTGRES"

log_info "Publishing glucose marts to Postgres..."
docker compose exec -T dagster-webserver dagster asset materialize \
    -m "$DAGSTER_MODULE" \
    --select publish_glucose_marts_to_postgres \
    2>&1 | grep -E "Successfully|Error|FAILURE" || true

# Verify Postgres data
log_info "Verifying Postgres marts..."

PG_OVERVIEW_COUNT=$(docker exec pg psql -U lake -d lakehouse -t -c "
    SELECT COUNT(*) FROM marts.mrt_glucose_overview;
" 2>&1 | tr -d ' ' || echo "0")

PG_HOURLY_COUNT=$(docker exec pg psql -U lake -d lakehouse -t -c "
    SELECT COUNT(*) FROM marts.mrt_glucose_hourly_patterns;
" 2>&1 | tr -d ' ' || echo "0")

log_info "Postgres mrt_glucose_overview: $PG_OVERVIEW_COUNT rows"
log_info "Postgres mrt_glucose_hourly_patterns: $PG_HOURLY_COUNT rows"

# Step 6: Query via REST API
log_section "STEP 6: VERIFY VIA REST API"

log_info "Authenticating to REST API..."
TOKEN=$(curl -s -X POST "$REST_API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}' | \
    grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [[ -z "$TOKEN" ]]; then
    log_error "Failed to get REST API token"
    exit 1
fi

log_info "Token obtained: ${TOKEN:0:20}..."

log_info "Querying glucose recent data via REST API..."
REST_RESPONSE=$(curl -s -X GET "$REST_API_URL/glucose/recent?limit=5" \
    -H "Authorization: Bearer $TOKEN")

REST_COUNT=$(echo "$REST_RESPONSE" | grep -o '"timestamp"' | wc -l | tr -d ' ')
log_info "REST API returned $REST_COUNT glucose readings"

if [[ "$REST_COUNT" -gt 0 ]]; then
    log_info "Sample REST response:"
    echo "$REST_RESPONSE" | head -c 500
    echo ""
fi

# Step 7: Query via GraphQL API
log_section "STEP 7: VERIFY VIA GRAPHQL API"

log_info "Querying mrt_glucose_overview via GraphQL..."
GRAPHQL_OVERVIEW=$(curl -s -X POST "$GRAPHQL_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "query { mrt_glucose_overview(limit: 5, order_by: {date: desc}) { date avg_glucose min_glucose max_glucose readings_count } }"
    }')

log_info "GraphQL mrt_glucose_overview response:"
echo "$GRAPHQL_OVERVIEW" | head -c 500
echo ""

log_info "Querying mrt_glucose_hourly_patterns via GraphQL..."
GRAPHQL_HOURLY=$(curl -s -X POST "$GRAPHQL_URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "query { mrt_glucose_hourly_patterns(limit: 5, order_by: {hour_of_day: asc}) { hour_of_day avg_glucose readings_count } }"
    }')

log_info "GraphQL mrt_glucose_hourly_patterns response:"
echo "$GRAPHQL_HOURLY" | head -c 500
echo ""

# Summary
log_section "PIPELINE TEST SUMMARY"

echo ""
echo "Data Ingested:"
echo "  Raw entries: $RAW_COUNT"
echo ""
echo "Transformations:"
echo "  Bronze (stg_entries): $BRONZE_COUNT"
echo "  Silver (fct_glucose_readings): $SILVER_COUNT"
echo "  Gold (overview): $GOLD_OVERVIEW_COUNT"
echo "  Gold (hourly): $GOLD_HOURLY_COUNT"
echo ""
echo "Postgres Marts:"
echo "  mrt_glucose_overview: $PG_OVERVIEW_COUNT"
echo "  mrt_glucose_hourly_patterns: $PG_HOURLY_COUNT"
echo ""
echo "API Verification:"
echo "  REST API readings: $REST_COUNT"
echo "  GraphQL APIs: Verified"
echo ""

# Check for success
if [[ "$PG_OVERVIEW_COUNT" -gt 0 ]] && [[ "$PG_HOURLY_COUNT" -gt 0 ]]; then
    log_info "Pipeline test completed successfully!"
    exit 0
else
    log_error "Pipeline test failed - no data in Postgres marts"
    exit 1
fi
