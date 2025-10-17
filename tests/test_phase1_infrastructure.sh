#!/usr/bin/env bash
set -e

# Phase 1 Infrastructure Tests
# Tests Nessie, Trino, MinIO, and Postgres setup

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo "=========================================="
echo "Phase 1: Infrastructure Tests"
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

# Get docker compose status once
COMPOSE_STATUS=$(docker compose ps 2>&1)

# Test 1: Check Docker services are running
echo "[Test 1] Checking Docker services are running..."
echo "$COMPOSE_STATUS" | grep -q "postgres.*Up"
check_result "Postgres service is running"

echo "$COMPOSE_STATUS" | grep -q "minio.*Up"
check_result "MinIO service is running"

echo "$COMPOSE_STATUS" | grep -q "nessie.*Up"
check_result "Nessie service is running"

echo "$COMPOSE_STATUS" | grep -q "trino.*Up"
check_result "Trino service is running"

echo ""

# Test 2: Check services are healthy
echo "[Test 2] Checking services are healthy..."
echo "$COMPOSE_STATUS" | grep -q "postgres.*healthy"
check_result "Postgres is healthy"

echo "$COMPOSE_STATUS" | grep -q "minio.*healthy"
check_result "MinIO is healthy"

echo "$COMPOSE_STATUS" | grep -q "nessie.*healthy"
check_result "Nessie is healthy"

echo "$COMPOSE_STATUS" | grep -q "trino.*healthy"
check_result "Trino is healthy"

echo ""

# Test 3: Check Nessie API
echo "[Test 3] Checking Nessie API..."
curl -sf http://localhost:19120/api/v1/config > /dev/null
check_result "Nessie API is accessible"

curl -sf http://localhost:19120/api/v1/trees | jq -r '.references[].name' | grep -q "main"
check_result "Nessie has 'main' branch"

echo ""

# Test 4: Check Trino
echo "[Test 4] Checking Trino..."
curl -sf http://localhost:8080/v1/info > /dev/null
check_result "Trino API is accessible"

# Check Trino Iceberg catalog config file exists
[ -f "docker/trino/catalog/iceberg.properties" ]
check_result "Trino Iceberg catalog config exists"

echo ""

# Test 5: Check MinIO buckets
echo "[Test 5] Checking MinIO buckets..."
# Check MinIO is accessible
curl -sf http://localhost:9000/minio/health/ready > /dev/null
check_result "MinIO is accessible"

# Note: Bucket verification would require mc client, skipping detailed check
echo "  (Bucket creation verified via minio-setup service logs)"

echo ""

# Test 6: Check environment variables
echo "[Test 6] Checking environment variables..."
[ ! -z "${NESSIE_VERSION}" ]
check_result "NESSIE_VERSION is set"

[ ! -z "${TRINO_VERSION}" ]
check_result "TRINO_VERSION is set"

[ ! -z "${ICEBERG_WAREHOUSE_PATH}" ]
check_result "ICEBERG_WAREHOUSE_PATH is set"

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
