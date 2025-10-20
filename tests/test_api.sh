#!/bin/bash
# API Integration Tests

set -e

echo "=== Cascade API Integration Tests ==="
echo

TESTS_PASSED=0
TESTS_FAILED=0

API_URL="http://localhost:8000"
HASURA_URL="http://localhost:8081"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

# Check if services are running
check_service() {
    local url=$1
    local name=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        pass "$name is running"
        return 0
    else
        fail "$name is not running (start with 'make up-api')"
        return 1
    fi
}

# Test HTTP endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    local headers=$6

    local response
    local status

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" $headers "$API_URL$endpoint" 2>&1)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST $headers \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint" 2>&1)
    fi

    status=$(echo "$response" | tail -n1)

    if [ "$status" = "$expected_status" ]; then
        pass "$description (HTTP $status)"
        echo "$response" | head -n -1
        return 0
    else
        fail "$description (Expected $expected_status, got $status)"
        echo "$response" | head -n -1
        return 1
    fi
}

# Test 1-5: Service Health Checks
echo "[1-5] Service Health Checks..."
check_service "$API_URL/health" "FastAPI"
check_service "$HASURA_URL/healthz" "Hasura"

# Test 6: API root endpoint
echo
echo "[6] Testing API root endpoint..."
if curl -sf "$API_URL/" | grep -q "Cascade Lakehouse API"; then
    pass "API root endpoint returns correct service name"
else
    fail "API root endpoint did not return expected response"
fi

# Test 7: Health endpoint (no auth)
echo
echo "[7] Testing health endpoint (no auth required)..."
if curl -sf "$API_URL/api/v1/metadata/health" | grep -q "healthy"; then
    pass "Health endpoint accessible without auth"
else
    fail "Health endpoint failed"
fi

# Test 8-9: Authentication
echo
echo "[8-9] Testing authentication..."

# Test admin login
ADMIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

if echo "$ADMIN_RESPONSE" | grep -q "access_token"; then
    pass "Admin login successful"
    ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    fail "Admin login failed"
    echo "$ADMIN_RESPONSE"
fi

# Test analyst login
ANALYST_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"analyst","password":"analyst123"}')

if echo "$ANALYST_RESPONSE" | grep -q "access_token"; then
    pass "Analyst login successful"
    ANALYST_TOKEN=$(echo "$ANALYST_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    fail "Analyst login failed"
    echo "$ANALYST_RESPONSE"
fi

# Test 10: Invalid login
echo
echo "[10] Testing invalid login..."
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"invalid","password":"wrong"}')

INVALID_STATUS=$(echo "$INVALID_RESPONSE" | tail -n1)
if [ "$INVALID_STATUS" = "401" ]; then
    pass "Invalid login correctly rejected (401)"
else
    fail "Invalid login should return 401, got $INVALID_STATUS"
fi

# Test 11: Protected endpoint without auth
echo
echo "[11] Testing protected endpoint without auth..."
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/metadata/user/me")
UNAUTH_STATUS=$(echo "$UNAUTH_RESPONSE" | tail -n1)

if [ "$UNAUTH_STATUS" = "403" ] || [ "$UNAUTH_STATUS" = "401" ]; then
    pass "Protected endpoint requires auth (HTTP $UNAUTH_STATUS)"
else
    fail "Protected endpoint should require auth, got $UNAUTH_STATUS"
fi

# Test 12: User info endpoint
echo
echo "[12] Testing user info endpoint..."
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$API_URL/api/v1/metadata/user/me")

if echo "$USER_RESPONSE" | grep -q "admin"; then
    pass "User info endpoint returns correct user"
else
    fail "User info endpoint failed"
    echo "$USER_RESPONSE"
fi

# Test 13: Cache stats endpoint
echo
echo "[13] Testing cache stats endpoint..."
CACHE_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$API_URL/api/v1/metadata/cache/stats")

if echo "$CACHE_RESPONSE" | grep -q "total_entries"; then
    pass "Cache stats endpoint working"
else
    fail "Cache stats endpoint failed"
    echo "$CACHE_RESPONSE"
fi

# Test 14-16: Glucose endpoints (may fail if no data)
echo
echo "[14-16] Testing glucose endpoints (may fail if no data ingested)..."

# Glucose readings
READINGS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    "$API_URL/api/v1/glucose/readings?limit=10")
READINGS_STATUS=$(echo "$READINGS_RESPONSE" | tail -n1)

if [ "$READINGS_STATUS" = "200" ]; then
    pass "Glucose readings endpoint accessible"
else
    fail "Glucose readings endpoint failed ($READINGS_STATUS)"
fi

# Hourly patterns
PATTERNS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    "$API_URL/api/v1/glucose/hourly-patterns")
PATTERNS_STATUS=$(echo "$PATTERNS_RESPONSE" | tail -n1)

if [ "$PATTERNS_STATUS" = "200" ]; then
    pass "Hourly patterns endpoint accessible"
else
    fail "Hourly patterns endpoint failed ($PATTERNS_STATUS)"
fi

# Statistics
STATS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    "$API_URL/api/v1/glucose/statistics?period=7d")
STATS_STATUS=$(echo "$STATS_RESPONSE" | tail -n1)

if [ "$STATS_STATUS" = "200" ]; then
    pass "Statistics endpoint accessible"
else
    fail "Statistics endpoint failed ($STATS_STATUS)"
fi

# Test 17: Iceberg tables list
echo
echo "[17] Testing Iceberg tables list..."
TABLES_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    "$API_URL/api/v1/iceberg/tables")
TABLES_STATUS=$(echo "$TABLES_RESPONSE" | tail -n1)

if [ "$TABLES_STATUS" = "200" ]; then
    pass "Iceberg tables list endpoint accessible"
else
    fail "Iceberg tables list failed ($TABLES_STATUS)"
fi

# Test 18: Admin-only SQL endpoint (analyst should be denied)
echo
echo "[18] Testing admin-only SQL endpoint with analyst user..."
ANALYST_SQL_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ANALYST_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"SELECT 1","engine":"postgres"}' \
    "$API_URL/api/v1/query/sql")
ANALYST_SQL_STATUS=$(echo "$ANALYST_SQL_RESPONSE" | tail -n1)

if [ "$ANALYST_SQL_STATUS" = "403" ]; then
    pass "SQL endpoint correctly denies analyst access"
else
    fail "SQL endpoint should deny analyst (403), got $ANALYST_SQL_STATUS"
fi

# Test 19: Admin SQL endpoint (admin should succeed)
echo
echo "[19] Testing admin SQL endpoint with admin user..."
ADMIN_SQL_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"SELECT 1 as test","engine":"postgres"}' \
    "$API_URL/api/v1/query/sql")
ADMIN_SQL_STATUS=$(echo "$ADMIN_SQL_RESPONSE" | tail -n1)

if [ "$ADMIN_SQL_STATUS" = "200" ]; then
    pass "SQL endpoint works with admin user"
else
    fail "SQL endpoint failed for admin ($ADMIN_SQL_STATUS)"
    echo "$ADMIN_SQL_RESPONSE" | head -n -1
fi

# Test 20: SQL injection protection
echo
echo "[20] Testing SQL injection protection..."
INJECTION_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"DROP TABLE users","engine":"postgres"}' \
    "$API_URL/api/v1/query/sql")
INJECTION_STATUS=$(echo "$INJECTION_RESPONSE" | tail -n1)

if [ "$INJECTION_STATUS" = "400" ]; then
    pass "SQL injection protection working (DROP blocked)"
else
    fail "SQL injection protection failed (should return 400)"
fi

# Test 21: OpenAPI docs
echo
echo "[21] Testing OpenAPI documentation..."
if curl -sf "$API_URL/docs" | grep -q "Swagger"; then
    pass "Swagger UI accessible"
else
    fail "Swagger UI not accessible"
fi

# Test 22: OpenAPI JSON
echo
echo "[22] Testing OpenAPI JSON spec..."
if curl -sf "$API_URL/openapi.json" | grep -q "openapi"; then
    pass "OpenAPI JSON spec available"
else
    fail "OpenAPI JSON spec not available"
fi

# Test 23: Hasura health
echo
echo "[23] Testing Hasura health endpoint..."
if curl -sf "$HASURA_URL/healthz" | grep -q "OK"; then
    pass "Hasura health check passed"
else
    fail "Hasura health check failed"
fi

# Test 24: Hasura GraphQL endpoint (with admin secret)
echo
echo "[24] Testing Hasura GraphQL endpoint..."
HASURA_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "x-hasura-admin-secret: cascade-admin-secret-change-me" \
    -H "Content-Type: application/json" \
    -d '{"query":"{ __schema { queryType { name } } }"}' \
    "$HASURA_URL/v1/graphql")
HASURA_STATUS=$(echo "$HASURA_RESPONSE" | tail -n1)

if [ "$HASURA_STATUS" = "200" ]; then
    pass "Hasura GraphQL endpoint accessible"
else
    fail "Hasura GraphQL endpoint failed ($HASURA_STATUS)"
fi

# Test 25: Hasura with JWT token
echo
echo "[25] Testing Hasura with JWT token..."
HASURA_JWT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"{ __schema { queryType { name } } }"}' \
    "$HASURA_URL/v1/graphql")
HASURA_JWT_STATUS=$(echo "$HASURA_JWT_RESPONSE" | tail -n1)

if [ "$HASURA_JWT_STATUS" = "200" ]; then
    pass "Hasura accepts JWT tokens from FastAPI"
else
    fail "Hasura JWT authentication failed ($HASURA_JWT_STATUS)"
    echo "$HASURA_JWT_RESPONSE" | head -n -1
fi

# Summary
echo
echo "=== Test Summary ==="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All API tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Review the output above.${NC}"
    exit 1
fi
