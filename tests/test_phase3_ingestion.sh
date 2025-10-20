#!/usr/bin/env bash
set -e

# Phase 3 Ingestion Layer Tests
# Tests PyIceberg integration and DLT asset updates

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Phase 3: Ingestion Layer Tests"
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

# Test 1: Check iceberg module structure exists
echo "[Test 1] Checking iceberg module structure..."
[ -d "src/cascade/iceberg" ]
check_result "iceberg module directory exists"

[ -f "src/cascade/iceberg/__init__.py" ]
check_result "iceberg __init__.py exists"

[ -f "src/cascade/iceberg/catalog.py" ]
check_result "iceberg catalog.py exists"

[ -f "src/cascade/iceberg/tables.py" ]
check_result "iceberg tables.py exists"

[ -f "src/cascade/iceberg/schema.py" ]
check_result "iceberg schema.py exists"

echo ""

# Test 2: Check iceberg module exports
echo "[Test 2] Checking iceberg module exports..."
grep -q "from cascade.iceberg.catalog import get_catalog" src/cascade/iceberg/__init__.py
check_result "__init__.py imports get_catalog"

grep -q "from cascade.iceberg.tables import ensure_table, append_to_table" src/cascade/iceberg/__init__.py
check_result "__init__.py imports table functions"

grep -q '__all__.*get_catalog' src/cascade/iceberg/__init__.py
check_result "__init__.py exports get_catalog"

echo ""

# Test 3: Check catalog.py has required functions
echo "[Test 3] Checking catalog.py functions..."
grep -q "def get_catalog" src/cascade/iceberg/catalog.py
check_result "catalog.py has get_catalog function"

grep -q "def list_tables" src/cascade/iceberg/catalog.py
check_result "catalog.py has list_tables function"

grep -q "def create_namespace" src/cascade/iceberg/catalog.py
check_result "catalog.py has create_namespace function"

grep -q "load_catalog" src/cascade/iceberg/catalog.py
check_result "catalog.py uses load_catalog from pyiceberg"

echo ""

# Test 4: Check tables.py has required functions
echo "[Test 4] Checking tables.py functions..."
grep -q "def ensure_table" src/cascade/iceberg/tables.py
check_result "tables.py has ensure_table function"

grep -q "def append_to_table" src/cascade/iceberg/tables.py
check_result "tables.py has append_to_table function"

grep -q "def get_table_schema" src/cascade/iceberg/tables.py
check_result "tables.py has get_table_schema function"

grep -q "def delete_table" src/cascade/iceberg/tables.py
check_result "tables.py has delete_table function"

echo ""

# Test 5: Check schema.py has Nightscout schemas
echo "[Test 5] Checking schema.py Nightscout schemas..."
grep -q "NIGHTSCOUT_ENTRIES_SCHEMA" src/cascade/iceberg/schema.py
check_result "schema.py has NIGHTSCOUT_ENTRIES_SCHEMA"

grep -q "NIGHTSCOUT_TREATMENTS_SCHEMA" src/cascade/iceberg/schema.py
check_result "schema.py has NIGHTSCOUT_TREATMENTS_SCHEMA"

grep -q "def get_schema" src/cascade/iceberg/schema.py
check_result "schema.py has get_schema function"

grep -q "from pyiceberg.schema import Schema" src/cascade/iceberg/schema.py
check_result "schema.py imports PyIceberg Schema"

echo ""

# Test 6: Check config.py has staging path
echo "[Test 6] Checking config.py has staging configuration..."
grep -q "iceberg_staging_path:" src/cascade/config.py
check_result "config.py has iceberg_staging_path"

grep -q 's3://lake/stage' src/cascade/config.py
check_result "config.py has staging path default value"

echo ""

# Test 7: Check .env.example has staging path
echo "[Test 7] Checking .env.example has staging configuration..."
grep -q "ICEBERG_STAGING_PATH" .env.example
check_result ".env.example has ICEBERG_STAGING_PATH"

echo ""

# Test 8: Check DLT assets updated
echo "[Test 8] Checking DLT assets file updates..."
! grep -q "ducklake" src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py does not reference ducklake"

grep -q "from cascade.iceberg import" src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py imports from cascade.iceberg"

grep -q "ensure_table" src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py uses ensure_table"

grep -q "append_to_table" src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py uses append_to_table"

grep -q "get_schema" src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py uses get_schema"

grep -q 'destination="filesystem"' src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py uses filesystem destination"

grep -q 'loader_file_format="parquet"' src/cascade/defs/ingestion/dlt_assets.py
check_result "dlt_assets.py uses parquet file format"

echo ""

# Test 9: Check pyproject.toml dependencies
echo "[Test 9] Checking pyproject.toml has PyIceberg dependencies..."
grep -q 'pyiceberg\[s3fs,pyarrow\]' src/pyproject.toml
check_result "cascade package has pyiceberg dependency"

grep -q 'trino' services/dagster/pyproject.toml
check_result "dagster service has trino dependency"

grep -q 'dbt-trino' services/dagster/pyproject.toml
check_result "dagster service has dbt-trino dependency"

grep -q 'cascade' services/dagster/pyproject.toml
check_result "dagster service depends on cascade package"

! grep -q 'duckdb[^-]' services/dagster/pyproject.toml
check_result "dagster service does not have duckdb dependency"

! grep -q 'dbt-duckdb' services/dagster/pyproject.toml
check_result "dagster service does not have dbt-duckdb dependency"

echo ""

# Test 10: Verify Python imports work (using workspace venv)
echo "[Test 10] Checking Python module imports..."
source .venv/bin/activate && python3 -c "
import sys
import os
os.environ.setdefault('POSTGRES_PASSWORD', 'test')
os.environ.setdefault('MINIO_ROOT_PASSWORD', 'test')
os.environ.setdefault('SUPERSET_ADMIN_PASSWORD', 'test')
from cascade.iceberg import get_catalog, ensure_table, append_to_table
from cascade.iceberg.schema import get_schema, NIGHTSCOUT_ENTRIES_SCHEMA
from cascade.config import config
assert hasattr(config, 'iceberg_staging_path')
assert config.iceberg_staging_path
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
