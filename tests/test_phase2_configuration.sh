#!/usr/bin/env bash
set -e

# Phase 2 Configuration Tests
# Tests configuration changes for Nessie, Trino, and Iceberg

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Phase 2: Configuration Tests"
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

# Test 1: Check config.py has Nessie configuration
echo "[Test 1] Checking config.py has Nessie configuration..."
grep -q "nessie_version:" src/cascade/config.py
check_result "config.py contains nessie_version"

grep -q "nessie_port:" src/cascade/config.py
check_result "config.py contains nessie_port"

grep -q "nessie_host:" src/cascade/config.py
check_result "config.py contains nessie_host"

grep -q "def nessie_uri" src/cascade/config.py
check_result "config.py contains nessie_uri property"

echo ""

# Test 2: Check config.py has Trino configuration
echo "[Test 2] Checking config.py has Trino configuration..."
grep -q "trino_version:" src/cascade/config.py
check_result "config.py contains trino_version"

grep -q "trino_port:" src/cascade/config.py
check_result "config.py contains trino_port"

grep -q "trino_host:" src/cascade/config.py
check_result "config.py contains trino_host"

grep -q "def trino_connection_string" src/cascade/config.py
check_result "config.py contains trino_connection_string property"

echo ""

# Test 3: Check config.py has Iceberg configuration
echo "[Test 3] Checking config.py has Iceberg configuration..."
grep -q "iceberg_warehouse_path:" src/cascade/config.py
check_result "config.py contains iceberg_warehouse_path"

grep -q "iceberg_default_namespace:" src/cascade/config.py
check_result "config.py contains iceberg_default_namespace"

echo ""

# Test 4: Check config.py does NOT have DuckLake configuration
echo "[Test 4] Checking config.py does NOT have DuckLake configuration..."
! grep -q "ducklake_catalog_database:" src/cascade/config.py
check_result "config.py does not contain ducklake_catalog_database"

! grep -q "ducklake_data_path" src/cascade/config.py
check_result "config.py does not contain ducklake_data_path property"

echo ""

# Test 5: Check docker-compose has Nessie/Trino/Iceberg env vars for Dagster
echo "[Test 5] Checking docker-compose Dagster environment variables..."
grep -A 30 "dagster-webserver:" docker-compose.yml | grep -q "NESSIE_VERSION"
check_result "dagster-webserver has NESSIE_VERSION"

grep -A 30 "dagster-webserver:" docker-compose.yml | grep -q "TRINO_VERSION"
check_result "dagster-webserver has TRINO_VERSION"

grep -A 30 "dagster-webserver:" docker-compose.yml | grep -q "ICEBERG_WAREHOUSE_PATH"
check_result "dagster-webserver has ICEBERG_WAREHOUSE_PATH"

grep -A 30 "dagster-daemon:" docker-compose.yml | grep -q "NESSIE_VERSION"
check_result "dagster-daemon has NESSIE_VERSION"

grep -A 30 "dagster-daemon:" docker-compose.yml | grep -q "TRINO_VERSION"
check_result "dagster-daemon has TRINO_VERSION"

grep -A 30 "dagster-daemon:" docker-compose.yml | grep -q "ICEBERG_WAREHOUSE_PATH"
check_result "dagster-daemon has ICEBERG_WAREHOUSE_PATH"

echo ""

# Test 6: Check docker-compose does NOT have DuckLake env vars
echo "[Test 6] Checking docker-compose does NOT have DuckLake env vars..."
! grep -A 30 "dagster-webserver:" docker-compose.yml | grep -q "DUCKLAKE_CATALOG_ALIAS"
check_result "dagster-webserver does not have DUCKLAKE_CATALOG_ALIAS"

! grep -A 30 "dagster-daemon:" docker-compose.yml | grep -q "DUCKLAKE_CATALOG_DATABASE"
check_result "dagster-daemon does not have DUCKLAKE_CATALOG_DATABASE"

echo ""

# Test 7: Verify configuration can be imported (Python syntax check)
echo "[Test 7] Checking config.py can be imported..."
cd src && python3 -c "from cascade.config import config; assert config.nessie_uri; assert config.trino_connection_string" 2>/dev/null && cd ..
check_result "config.py imports successfully and has new properties"

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
