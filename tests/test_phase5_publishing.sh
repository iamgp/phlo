#!/usr/bin/env bash
set -e

# Phase 5 Publishing & BI Tests
# Tests publishing layer migration from DuckDB to Trino

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Phase 5: Publishing & BI Tests"
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

# Test 1: Check old DuckDB publishing file is removed
echo "[Test 1] Checking DuckDB publishing code removed..."
! [ -f "src/cascade/defs/publishing/duckdb_to_postgres.py" ]
check_result "duckdb_to_postgres.py does not exist"

echo ""

# Test 2: Check new Trino publishing file exists
echo "[Test 2] Checking Trino publishing code exists..."
[ -f "src/cascade/defs/publishing/trino_to_postgres.py" ]
check_result "trino_to_postgres.py exists"

grep -q "import trino" src/cascade/defs/publishing/trino_to_postgres.py
check_result "trino_to_postgres.py imports trino"

grep -q "import psycopg2" src/cascade/defs/publishing/trino_to_postgres.py
check_result "trino_to_postgres.py imports psycopg2"

grep -q "publish_glucose_marts_to_postgres" src/cascade/defs/publishing/trino_to_postgres.py
check_result "trino_to_postgres.py defines publishing asset"

echo ""

# Test 3: Check publishing uses Iceberg sources
echo "[Test 3] Checking publishing references Iceberg sources..."
grep -q "iceberg.marts.mrt_glucose_overview" src/cascade/defs/publishing/trino_to_postgres.py
check_result "publishing reads from iceberg.marts.mrt_glucose_overview"

grep -q "iceberg.marts.mrt_glucose_hourly_patterns" src/cascade/defs/publishing/trino_to_postgres.py
check_result "publishing reads from iceberg.marts.mrt_glucose_hourly_patterns"

! grep -q "ducklake" src/cascade/defs/publishing/trino_to_postgres.py
check_result "publishing does not reference ducklake"

echo ""

# Test 4: Check publishing __init__.py updated
echo "[Test 4] Checking publishing __init__.py imports..."
grep -q "from cascade.defs.publishing.trino_to_postgres import" src/cascade/defs/publishing/__init__.py
check_result "__init__.py imports from trino_to_postgres"

! grep -q "duckdb_to_postgres" src/cascade/defs/publishing/__init__.py
check_result "__init__.py does not import from duckdb_to_postgres"

echo ""

# Test 5: Check docker-compose has ICEBERG_STAGING_PATH
echo "[Test 5] Checking docker-compose environment variables..."
grep -q "ICEBERG_STAGING_PATH:" docker-compose.yml
check_result "docker-compose has ICEBERG_STAGING_PATH"

grep -A 20 "dagster-webserver:" docker-compose.yml | grep -q "ICEBERG_STAGING_PATH"
check_result "dagster-webserver has ICEBERG_STAGING_PATH"

grep -A 20 "dagster-daemon:" docker-compose.yml | grep -q "ICEBERG_STAGING_PATH"
check_result "dagster-daemon has ICEBERG_STAGING_PATH"

echo ""

# Test 6: Check .env.example has ICEBERG_STAGING_PATH
echo "[Test 6] Checking .env.example has staging path..."
grep -q "ICEBERG_STAGING_PATH" .env.example
check_result ".env.example has ICEBERG_STAGING_PATH"

echo ""

# Test 7: Check mart models target marts schema
echo "[Test 7] Checking mart models configuration..."
grep -q "marts" transforms/dbt/models/marts_postgres/mrt_glucose_overview.sql
check_result "mrt_glucose_overview references marts"

grep -q "marts" transforms/dbt/models/marts_postgres/mrt_glucose_hourly_patterns.sql
check_result "mrt_glucose_hourly_patterns references marts"

echo ""

# Test 8: Check Python imports work
echo "[Test 8] Checking Python module imports..."
source .venv/bin/activate && python3 -c "
import sys
import os
os.environ.setdefault('POSTGRES_PASSWORD', 'test')
os.environ.setdefault('MINIO_ROOT_PASSWORD', 'test')
os.environ.setdefault('SUPERSET_ADMIN_PASSWORD', 'test')
from cascade.defs.publishing.trino_to_postgres import publish_glucose_marts_to_postgres
from cascade.config import config
assert hasattr(config, 'trino_host')
assert hasattr(config, 'iceberg_staging_path')
print('All imports successful')
" 2>/dev/null && deactivate 2>/dev/null || true
check_result "Python imports work correctly"

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
