#!/bin/bash
# Phase 12: Observability Stack Test Suite

echo "=== Phase 12: Observability Stack Tests ==="
echo

TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
pass() {
    echo "✓ $1"
    ((TESTS_PASSED++))
}

fail() {
    echo "✗ $1"
    ((TESTS_FAILED++))
}

# Test 1: Docker compose observability profile defined
echo "[1/15] Checking docker-compose observability profile..."
if grep -q 'profiles: \["observability"' docker-compose.yml; then
    pass "Observability profile defined in docker-compose.yml"
else
    fail "Observability profile not found"
fi

# Test 2: Prometheus configuration exists
echo "[2/15] Checking Prometheus configuration..."
if [ -f docker/prometheus/prometheus.yml ]; then
    pass "Prometheus configuration file exists"
else
    fail "Prometheus configuration missing"
fi

# Test 3: Loki configuration exists
echo "[3/15] Checking Loki configuration..."
if [ -f docker/loki/loki-config.yml ]; then
    pass "Loki configuration file exists"
else
    fail "Loki configuration missing"
fi

# Test 4: Alloy configuration exists
echo "[4/15] Checking Alloy configuration..."
if [ -f docker/alloy/config.alloy ]; then
    pass "Alloy configuration file exists"
else
    fail "Alloy configuration missing"
fi

# Test 5: Grafana datasources provisioned
echo "[5/15] Checking Grafana datasource provisioning..."
if [ -f docker/grafana/provisioning/datasources/datasources.yml ]; then
    pass "Grafana datasources provisioning exists"
else
    fail "Grafana datasources provisioning missing"
fi

# Test 6: Grafana dashboards provisioned
echo "[6/15] Checking Grafana dashboard provisioning..."
if [ -f docker/grafana/provisioning/dashboards/dashboards.yml ]; then
    pass "Grafana dashboards provisioning exists"
else
    fail "Grafana dashboards provisioning missing"
fi

# Test 7: Overview dashboard exists
echo "[7/15] Checking Cascade Overview dashboard..."
if [ -f docker/grafana/dashboards/cascade-overview.json ]; then
    pass "Cascade Overview dashboard exists"
else
    fail "Cascade Overview dashboard missing"
fi

# Test 8: Infrastructure dashboard exists
echo "[8/15] Checking Infrastructure dashboard..."
if [ -f docker/grafana/dashboards/infrastructure.json ]; then
    pass "Infrastructure dashboard exists"
else
    fail "Infrastructure dashboard missing"
fi

# Test 9: Prometheus scrape configs
echo "[9/15] Checking Prometheus scrape configurations..."
EXPECTED_JOBS=("prometheus" "alloy" "minio" "postgres" "trino" "nessie" "dagster")
for job in "${EXPECTED_JOBS[@]}"; do
    if grep -q "job_name: '$job'" docker/prometheus/prometheus.yml; then
        pass "  - $job scrape config found"
    else
        fail "  - $job scrape config missing"
    fi
done

# Test 10: Dagster failure sensor exists
echo "[10/15] Checking Dagster failure sensor..."
if [ -f src/cascade/defs/sensors/failure_monitoring.py ]; then
    pass "Dagster failure monitoring sensors exist"
else
    fail "Dagster failure monitoring sensors missing"
fi

# Test 11: Sensors module exports
echo "[11/15] Checking sensors module exports..."
if [ -f src/cascade/defs/sensors/__init__.py ]; then
    if grep -q "build_defs" src/cascade/defs/sensors/__init__.py; then
        pass "Sensors module properly exports build_defs"
    else
        fail "Sensors module missing build_defs export"
    fi
else
    fail "Sensors __init__.py missing"
fi

# Test 12: Sensors integrated in definitions
echo "[12/15] Checking sensor integration in Dagster..."
if grep -q "from cascade.defs.sensors import build_defs as build_sensor_defs" src/cascade/definitions.py; then
    pass "Sensors imported in definitions.py"
else
    fail "Sensors not imported in definitions.py"
fi

if grep -q "build_sensor_defs()" src/cascade/definitions.py; then
    pass "Sensors merged in definitions"
else
    fail "Sensors not merged in definitions"
fi

# Test 13: Makefile observability targets
echo "[13/15] Checking Makefile observability targets..."
if grep -q "up-observability:" Makefile; then
    pass "Makefile has up-observability target"
else
    fail "Makefile missing up-observability target"
fi

if grep -q "health-observability:" Makefile; then
    pass "Makefile has health-observability target"
else
    fail "Makefile missing health-observability target"
fi

# Test 14: Environment variables
echo "[14/15] Checking observability environment variables..."
EXPECTED_VARS=("PROMETHEUS_VERSION" "LOKI_VERSION" "ALLOY_VERSION" "GRAFANA_VERSION")
for var in "${EXPECTED_VARS[@]}"; do
    if grep -q "^$var=" .env.example; then
        pass "  - $var defined in .env.example"
    else
        fail "  - $var missing in .env.example"
    fi
done

# Test 15: Documentation exists
echo "[15/15] Checking observability documentation..."
if [ -f docs/OBSERVABILITY.md ]; then
    pass "Observability documentation exists"
else
    fail "Observability documentation missing"
fi

# Summary
echo
echo "=== Test Summary ==="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ All Phase 12 tests passed!"
    exit 0
else
    echo "✗ Some tests failed. Review the output above."
    exit 1
fi
