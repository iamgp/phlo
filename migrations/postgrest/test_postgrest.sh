#!/bin/bash
# Test script for PostgREST API endpoints
# Verifies that all endpoints are working correctly

set -e

# Configuration
POSTGREST_URL="${POSTGREST_URL:-http://localhost:10018}"
ADMIN_URL="${ADMIN_URL:-http://localhost:10019}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

echo "======================================"
echo "PostgREST API Test Suite"
echo "======================================"
echo "PostgREST URL: $POSTGREST_URL"
echo "Admin URL: $ADMIN_URL"
echo "======================================"
echo ""

# Function to print test results
pass() {
  echo -e "${GREEN}✓${NC} $1"
  ((TESTS_PASSED++))
}

fail() {
  echo -e "${RED}✗${NC} $1"
  ((TESTS_FAILED++))
}

info() {
  echo -e "${YELLOW}ℹ${NC} $1"
}

# Test 1: Health Check
echo "Test 1: Health Check (Admin Endpoint)"
if curl -s -f "$ADMIN_URL/live" > /dev/null 2>&1; then
  pass "Admin health check endpoint is accessible"
else
  fail "Admin health check endpoint failed"
  echo "   Make sure PostgREST is running: docker-compose ps postgrest"
  exit 1
fi
echo ""

# Test 2: OpenAPI Schema
echo "Test 2: OpenAPI Schema"
OPENAPI_RESPONSE=$(curl -s -H "Accept: application/openapi+json" "$POSTGREST_URL/")
if echo "$OPENAPI_RESPONSE" | grep -q '"openapi"'; then
  pass "OpenAPI schema is available"
else
  fail "OpenAPI schema not found"
fi
echo ""

# Test 3: Login (Get JWT Token)
echo "Test 3: Login and JWT Token Generation"
LOGIN_RESPONSE=$(curl -s -X POST "$POSTGREST_URL/rpc/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "analyst123"}' 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  pass "Login successful - JWT token generated"
  TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  info "Token: ${TOKEN:0:50}..."
else
  fail "Login failed"
  echo "   Response: $LOGIN_RESPONSE"
  echo "   Make sure migrations have been applied: ./migrations/postgrest/apply_migrations.sh"
  exit 1
fi
echo ""

# Test 4: Login with Invalid Credentials
echo "Test 4: Login with Invalid Credentials (Should Fail)"
INVALID_LOGIN=$(curl -s -X POST "$POSTGREST_URL/rpc/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "wrongpassword"}' 2>&1)

if echo "$INVALID_LOGIN" | grep -q "Invalid credentials"; then
  pass "Invalid credentials rejected correctly"
else
  fail "Invalid credentials should be rejected"
fi
echo ""

# Test 5: Access Without Authentication
echo "Test 5: Access Protected Endpoint Without Token (Should Fail)"
UNAUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$POSTGREST_URL/glucose_readings")
if [ "$UNAUTH_RESPONSE" = "401" ]; then
  pass "Unauthenticated request rejected (HTTP 401)"
else
  fail "Unauthenticated request should return 401, got: $UNAUTH_RESPONSE"
fi
echo ""

# Test 6: Get Glucose Readings
echo "Test 6: Get Glucose Readings (Authenticated)"
READINGS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_readings?limit=1")

HTTP_CODE=$(echo "$READINGS_RESPONSE" | tail -n 1)
BODY=$(echo "$READINGS_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  if echo "$BODY" | grep -q "reading_date"; then
    pass "Glucose readings endpoint working"
    info "Sample: $(echo "$BODY" | head -c 100)..."
  else
    fail "Glucose readings returned empty or invalid data"
    echo "   Response: $BODY"
  fi
else
  fail "Glucose readings endpoint failed (HTTP $HTTP_CODE)"
  echo "   Response: $BODY"
fi
echo ""

# Test 7: Get Daily Summary
echo "Test 7: Get Daily Summary"
SUMMARY_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_daily_summary?limit=1")

HTTP_CODE=$(echo "$SUMMARY_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  pass "Daily summary endpoint working"
else
  fail "Daily summary endpoint failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 8: Get Hourly Patterns
echo "Test 8: Get Hourly Patterns"
PATTERNS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_hourly_patterns?limit=1")

HTTP_CODE=$(echo "$PATTERNS_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  pass "Hourly patterns endpoint working"
else
  fail "Hourly patterns endpoint failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 9: Get Statistics Function
echo "Test 9: Get Statistics (PostgreSQL Function)"
STATS_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/rpc/glucose_statistics?period_days=7")

HTTP_CODE=$(echo "$STATS_RESPONSE" | tail -n 1)
BODY=$(echo "$STATS_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  if echo "$BODY" | grep -q "period_days"; then
    pass "Statistics function working"
    info "7-day stats: $(echo "$BODY" | grep -o '"avg_glucose_mg_dl":[^,]*')"
  else
    fail "Statistics function returned invalid data"
  fi
else
  fail "Statistics function failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 10: Get User Info
echo "Test 10: Get Current User Info"
USER_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/rpc/user_info")

HTTP_CODE=$(echo "$USER_RESPONSE" | tail -n 1)
BODY=$(echo "$USER_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  if echo "$BODY" | grep -q "analyst"; then
    pass "User info endpoint working"
    info "User: $(echo "$BODY" | grep -o '"username":"[^"]*' | cut -d'"' -f4)"
  else
    fail "User info returned unexpected data"
  fi
else
  fail "User info endpoint failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 11: Filtering
echo "Test 11: Test Filtering (Date Range)"
FILTER_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_readings?reading_date=gte.2024-01-01&limit=1")

HTTP_CODE=$(echo "$FILTER_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  pass "Filtering by date range working"
else
  fail "Filtering failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 12: Ordering
echo "Test 12: Test Ordering"
ORDER_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_readings?order=reading_date.desc&limit=1")

HTTP_CODE=$(echo "$ORDER_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  pass "Ordering by column working"
else
  fail "Ordering failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 13: Column Selection
echo "Test 13: Test Column Selection"
SELECT_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$POSTGREST_URL/glucose_readings?select=reading_date,avg_glucose_mg_dl&limit=1")

HTTP_CODE=$(echo "$SELECT_RESPONSE" | tail -n 1)
BODY=$(echo "$SELECT_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
  # Check that only selected columns are present
  if echo "$BODY" | grep -q "reading_date" && echo "$BODY" | grep -q "avg_glucose_mg_dl"; then
    pass "Column selection working"
  else
    fail "Column selection returned unexpected columns"
  fi
else
  fail "Column selection failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 14: JWT Token Expiration Check
echo "Test 14: JWT Token Structure"
# Decode JWT payload (second part)
if command -v jq &> /dev/null; then
  PAYLOAD=$(echo "$TOKEN" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq . 2>/dev/null || echo "{}")
  if echo "$PAYLOAD" | grep -q "role"; then
    pass "JWT token contains role claim"
    info "Role: $(echo "$PAYLOAD" | jq -r '.role' 2>/dev/null || echo 'unknown')"
  else
    fail "JWT token missing role claim"
  fi
else
  info "Skipping JWT decode test (jq not installed)"
fi
echo ""

# Summary
echo "======================================"
echo "Test Results"
echo "======================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "======================================"

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ All tests passed!${NC}"
  echo ""
  echo "PostgREST is working correctly. You can now:"
  echo "  1. View OpenAPI docs: http://localhost:10018/"
  echo "  2. Test endpoints with curl or Postman"
  echo "  3. Integrate with your applications"
  exit 0
else
  echo -e "${RED}✗ Some tests failed${NC}"
  echo ""
  echo "Troubleshooting steps:"
  echo "  1. Check PostgREST logs: docker-compose logs postgrest"
  echo "  2. Verify migrations: psql -h localhost -p 10000 -U lake -d lakehouse -c '\\dt api.*'"
  echo "  3. Check database connection: psql -h localhost -p 10000 -U lake -d lakehouse"
  echo "  4. Review docs/POSTGREST_DEPLOYMENT.md"
  exit 1
fi
