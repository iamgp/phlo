#!/usr/bin/env bash
set -e

# Phase 4 Transformation Layer Tests
# Tests dbt configuration migration from dbt-duckdb to dbt-trino

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Phase 4: Transformation Layer Tests"
echo "=========================================="
echo ""

FAILED=0
PASSED=0

# Helper function to check test result
check_result() {
    local result=$?
    if [ $result -eq 0 ]; then
        echo "✓ PASS: $1"
        ((PASSED++))
    else
        echo "✗ FAIL: $1"
        ((FAILED++))
    fi
    return 0  # Don't exit on failure
}

# Test 1: Check dbt_project.yml has no DuckLake hooks
echo "[Test 1] Checking dbt_project.yml removed DuckLake hooks..."
! grep -q 'ducklake__bootstrap' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml does not reference ducklake__bootstrap"

! grep -q 'on-run-start' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml does not have on-run-start hook"

! grep -q 'pre-hook' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml does not have pre-hook"

! grep -q 'macro-paths' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml does not reference macro-paths"

echo ""

# Test 2: Check dbt_project.yml has correct model configuration
echo "[Test 2] Checking dbt_project.yml model configuration..."
grep -q 'bronze:' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml has bronze model config"

grep -q 'silver:' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml has silver model config"

grep -q 'gold:' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml has gold model config"

grep -q 'marts_postgres:' transforms/dbt/dbt_project.yml
check_result "dbt_project.yml has marts_postgres model config"

echo ""

# Test 3: Check profiles.yml uses Trino
echo "[Test 3] Checking profiles.yml has Trino configuration..."
grep -q 'type: trino' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml uses trino adapter"

grep -q 'catalog: iceberg' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml references iceberg catalog"

grep -q 'nessie.reference: dev' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml has dev branch configuration"

grep -q 'nessie.reference: main' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml has prod branch configuration"

! grep -q 'type: duckdb' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml does not reference duckdb"

echo ""

# Test 4: Check profiles.yml has postgres output
echo "[Test 4] Checking profiles.yml has postgres output..."
grep -q 'postgres:' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml has postgres output"

grep -q 'type: postgres' transforms/dbt/profiles/profiles.yml
check_result "profiles.yml postgres output uses postgres adapter"

echo ""

# Test 5: Check sources.yml references Iceberg
echo "[Test 5] Checking sources.yml uses Iceberg catalog..."
grep -q 'database: iceberg' transforms/dbt/models/sources/sources.yml
check_result "sources.yml references iceberg database"

grep -q 'schema: raw' transforms/dbt/models/sources/sources.yml
check_result "sources.yml references raw schema"

! grep -q 'ducklake' transforms/dbt/models/sources/sources.yml
check_result "sources.yml does not reference ducklake"

echo ""

# Test 6: Check bronze model uses Trino functions
echo "[Test 6] Checking bronze models use Trino-compatible SQL..."
grep -q 'from_unixtime' transforms/dbt/models/bronze/stg_entries.sql
check_result "stg_entries.sql uses from_unixtime for timestamp conversion"

! grep -q 'epoch_ms' transforms/dbt/models/bronze/stg_entries.sql
check_result "stg_entries.sql does not use DuckDB-specific epoch_ms"

grep -q 'mills' transforms/dbt/models/bronze/stg_entries.sql
check_result "stg_entries.sql references mills field from Iceberg"

echo ""

# Test 7: Check silver model uses Trino functions
echo "[Test 7] Checking silver models use Trino-compatible SQL..."
grep -q 'day_of_week' transforms/dbt/models/silver/fct_glucose_readings.sql
check_result "fct_glucose_readings.sql uses day_of_week function"

grep -q 'format_datetime' transforms/dbt/models/silver/fct_glucose_readings.sql
check_result "fct_glucose_readings.sql uses format_datetime for day names"

grep -q 'date_diff' transforms/dbt/models/silver/fct_glucose_readings.sql
check_result "fct_glucose_readings.sql uses date_diff for time calculations"

! grep -q 'dayname' transforms/dbt/models/silver/fct_glucose_readings.sql
check_result "fct_glucose_readings.sql does not use DuckDB-specific dayname"

echo ""

# Test 8: Check gold model uses Trino functions
echo "[Test 8] Checking gold models use Trino-compatible SQL..."
grep -q 'week(' transforms/dbt/models/gold/dim_date.sql
check_result "dim_date.sql uses week function"

grep -q 'format_datetime' transforms/dbt/models/gold/dim_date.sql
check_result "dim_date.sql uses format_datetime"

! grep -q 'dayname' transforms/dbt/models/gold/dim_date.sql
check_result "dim_date.sql does not use DuckDB-specific dayname"

echo ""

# Test 9: Check mart models use Trino-compatible SQL
echo "[Test 9] Checking marts use Trino-compatible SQL..."
grep -q "interval '90' day" transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql
check_result "mrt_glucose_overview.sql uses Trino interval syntax"

grep -q 'approx_percentile' transforms/dbt/models/marts_postgres/mrt_glucose_hourly_patterns.sql
check_result "mrt_glucose_hourly_patterns.sql uses approx_percentile"

! grep -q 'percentile_cont' transforms/dbt/models/marts_postgres/mrt_glucose_hourly_patterns.sql
check_result "mrt_glucose_hourly_patterns.sql does not use percentile_cont"

echo ""

# Test 10: Check no macros directory exists
echo "[Test 10] Checking macros directory was removed..."
! [ -d "transforms/dbt/macros" ]
check_result "macros directory does not exist"

echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "PASSED: $PASSED"
echo "FAILED: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "Some tests failed!"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
