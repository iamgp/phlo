#!/usr/bin/env bash
set -euo pipefail

# Phase 10: DuckDB Iceberg Extension Test
# Tests DuckDB's ability to query Iceberg tables directly from MinIO

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

section() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

section "Phase 10: DuckDB Iceberg Extension Tests"

# Check if services are running
check_service() {
    local service=$1
    if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# 10.1: Documentation exists
section "10.1: Documentation"

if [ -f "docs/duckdb-iceberg-queries.md" ]; then
    pass "DuckDB Iceberg documentation exists"
else
    fail "DuckDB Iceberg documentation missing"
fi

if grep -q "INSTALL iceberg" docs/duckdb-iceberg-queries.md; then
    pass "Documentation includes extension installation"
else
    fail "Documentation missing extension installation"
fi

if grep -q "s3_endpoint" docs/duckdb-iceberg-queries.md; then
    pass "Documentation includes S3/MinIO configuration"
else
    fail "Documentation missing S3/MinIO configuration"
fi

if grep -q "iceberg_scan" docs/duckdb-iceberg-queries.md; then
    pass "Documentation includes iceberg_scan examples"
else
    fail "Documentation missing iceberg_scan examples"
fi

# 10.2: Python script exists
section "10.2: Test Scripts"

if [ -f "tests/scripts/test_duckdb_iceberg.py" ]; then
    pass "Python test script exists"
else
    info "Python test script not found (will be created)"
fi

# 10.3: Integration tests (if services are running)
section "10.3: DuckDB Integration Tests"

if check_service minio; then
    info "MinIO is running, performing integration tests"

    # Check if Python is available
    if command -v python3 &> /dev/null; then
        info "Running DuckDB integration test..."

        # Run the Python test script
        if [ -f "tests/scripts/test_duckdb_iceberg.py" ]; then
            if python3 tests/scripts/test_duckdb_iceberg.py 2>&1; then
                pass "DuckDB can query Iceberg tables from MinIO"
            else
                fail "DuckDB integration test failed"
            fi
        else
            info "Python test script not found, skipping integration test"
        fi
    else
        info "Python3 not available, skipping integration tests"
    fi
else
    info "MinIO not running - skipping integration tests"
    info "Run 'make up-all' to start services for integration tests"
fi

section "Test Summary"
echo ""
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All Phase 10 tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some Phase 10 tests failed.${NC}"
    exit 1
fi
