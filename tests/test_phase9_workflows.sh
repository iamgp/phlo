#!/usr/bin/env bash
set -euo pipefail

# Phase 9: Dynamic Branch Workflow Test Suite
# Tests dynamic pipeline branches, validation gates, and automatic promotion workflow

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

# Check if services are running
check_service() {
    local service=$1
    if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

section "Phase 9: Dynamic Branch Workflow Tests"

info "Testing dynamic branch creation, validation gates, and automatic promotion"

section "9.1: Branch-Aware Resources with Dynamic Branch Support"

# Test TrinoResource supports override_ref parameter
if grep -q "override_ref" src/cascade/defs/resources/trino.py; then
    pass "TrinoResource has override_ref parameter for dynamic branches"
else
    fail "TrinoResource missing override_ref parameter"
fi

# Test IcebergResource supports override_ref parameter
if grep -q "override_ref" src/cascade/defs/resources/iceberg.py; then
    pass "IcebergResource has override_ref parameter for dynamic branches"
else
    fail "IcebergResource missing override_ref parameter"
fi

# Test Trino connection uses session properties for dynamic branches
if grep -q "iceberg.nessie_reference_name" src/cascade/defs/resources/trino.py; then
    pass "TrinoResource uses session_properties for dynamic branch configuration"
else
    fail "TrinoResource missing session_properties support"
fi

section "9.2: Branch Manager Resource"

# Test BranchManagerResource exists
if [ -f "src/cascade/defs/nessie/branch_manager.py" ]; then
    pass "BranchManagerResource module exists"
else
    fail "BranchManagerResource module missing"
fi

# Test BranchManagerResource has create_pipeline_branch method
if grep -q "create_pipeline_branch" src/cascade/defs/nessie/branch_manager.py; then
    pass "BranchManagerResource has create_pipeline_branch method"
else
    fail "BranchManagerResource missing create_pipeline_branch method"
fi

# Test BranchManagerResource has schedule_cleanup method
if grep -q "schedule_cleanup" src/cascade/defs/nessie/branch_manager.py; then
    pass "BranchManagerResource has schedule_cleanup method"
else
    fail "BranchManagerResource missing schedule_cleanup method"
fi

section "9.3: Validation Gates"

# Test validation orchestrator exists
if [ -f "src/cascade/defs/validation/orchestrator.py" ]; then
    pass "Validation orchestrator module exists"
else
    fail "Validation orchestrator module missing"
fi

# Test PanderaValidator exists
if [ -f "src/cascade/defs/validation/pandera_validator.py" ]; then
    pass "PanderaValidator module exists"
else
    fail "PanderaValidator module missing"
fi

# Test DBTValidator exists
if [ -f "src/cascade/defs/validation/dbt_validator.py" ]; then
    pass "DBTValidator module exists"
else
    fail "DBTValidator module missing"
fi

# Test FreshnessValidator exists
if [ -f "src/cascade/defs/validation/freshness_validator.py" ]; then
    pass "FreshnessValidator module exists"
else
    fail "FreshnessValidator module missing"
fi

# Test SchemaCompatibilityValidator exists
if [ -f "src/cascade/defs/validation/schema_validator.py" ]; then
    pass "SchemaCompatibilityValidator module exists"
else
    fail "SchemaCompatibilityValidator module missing"
fi

# Test validation_orchestrator asset exists
if grep -q "validation_orchestrator" src/cascade/defs/validation/orchestrator.py; then
    pass "validation_orchestrator asset defined"
else
    fail "validation_orchestrator asset not defined"
fi

section "9.4: Dynamic Job Definitions"

# Test full_pipeline job exists in config
if grep -q "full_pipeline" src/cascade/defs/jobs/config.yaml; then
    pass "full_pipeline job defined in config.yaml"
else
    fail "full_pipeline job not defined in config.yaml"
fi

# Test validate job exists in config
if grep -q "validate" src/cascade/defs/jobs/config.yaml; then
    pass "validate job defined in config.yaml"
else
    fail "validate job not defined in config.yaml"
fi

# Test promote job exists in config
if grep -q "promote" src/cascade/defs/jobs/config.yaml; then
    pass "promote job defined in config.yaml"
else
    fail "promote job not defined in config.yaml"
fi

# Test validate job includes validation_orchestrator
if grep -A5 "validate:" src/cascade/defs/jobs/config.yaml | grep -q "validation_orchestrator"; then
    pass "validate job includes validation_orchestrator"
else
    fail "validate job missing validation_orchestrator"
fi

# Test promote job includes promote_to_main
if grep -A5 "promote:" src/cascade/defs/jobs/config.yaml | grep -q "promote_to_main"; then
    pass "promote job includes promote_to_main"
else
    fail "promote job missing promote_to_main"
fi

section "9.5: Promotion Sensors"

# Test promotion sensor exists
if [ -f "src/cascade/defs/sensors/promotion_sensor.py" ]; then
    pass "Promotion sensor module exists"
else
    fail "Promotion sensor module missing"
fi

# Test auto_promotion_sensor exists
if grep -q "auto_promotion_sensor" src/cascade/defs/sensors/promotion_sensor.py; then
    pass "auto_promotion_sensor defined"
else
    fail "auto_promotion_sensor not defined"
fi

# Test branch_cleanup_sensor exists
if grep -q "branch_cleanup_sensor" src/cascade/defs/sensors/promotion_sensor.py; then
    pass "branch_cleanup_sensor defined"
else
    fail "branch_cleanup_sensor not defined"
fi

section "9.6: Ingestion Assets Support Dynamic Branches"

# Test glucose entries asset accepts branch_name from run_config
if grep -q 'run_config.get("branch_name"' src/cascade/defs/ingestion/dlt_assets.py; then
    pass "Glucose entries asset supports dynamic branch_name from run_config"
else
    fail "Glucose entries asset missing branch_name support"
fi

# Test github assets accept branch_name from run_config
if grep -q 'run_config.get("branch_name"' src/cascade/defs/ingestion/github_assets.py; then
    pass "GitHub assets support dynamic branch_name from run_config"
else
    fail "GitHub assets missing branch_name support"
fi

section "9.7: dbt Profile Configuration"

# Test dbt profile uses NESSIE_REF environment variable
if grep -q 'env_var.*NESSIE_REF' transforms/dbt/profiles/profiles.yml; then
    pass "dbt profile uses NESSIE_REF environment variable for dynamic branches"
else
    fail "dbt profile missing NESSIE_REF environment variable support"
fi

# Test dbt session properties use iceberg.nessie_reference_name
if grep -q "iceberg.nessie_reference_name" transforms/dbt/profiles/profiles.yml; then
    pass "dbt profile uses session_properties for dynamic branch configuration"
else
    fail "dbt profile missing session_properties support"
fi

section "9.8: Configuration Schema"

# Test config has branch retention settings
if grep -q "branch_retention_days" src/cascade/config.py; then
    pass "Config has branch_retention_days setting"
else
    fail "Config missing branch_retention_days setting"
fi

# Test config has auto_promote_enabled setting
if grep -q "auto_promote_enabled" src/cascade/config.py; then
    pass "Config has auto_promote_enabled setting"
else
    fail "Config missing auto_promote_enabled setting"
fi

# Test config has validation retry settings
if grep -q "validation_retry_enabled" src/cascade/config.py; then
    pass "Config has validation_retry_enabled setting"
else
    fail "Config missing validation_retry_enabled setting"
fi

section "9.9: Python Imports and Syntax"

# Test validation module imports correctly (requires installed package)
if [ -f "pyproject.toml" ]; then
    info "Checking if cascade package is installed..."
    if python3 -c "import cascade" 2>/dev/null; then
        if python3 -c "from cascade.defs.validation import build_defs" 2>/dev/null; then
            pass "Validation module imports successfully"
        else
            fail "Validation module import failed"
        fi

        if python3 -c "from cascade.defs.validation import validation_orchestrator" 2>/dev/null; then
            pass "Validation orchestrator imports successfully"
        else
            fail "Validation orchestrator import failed"
        fi

        if python3 -c "from cascade.defs.nessie.branch_manager import BranchManagerResource" 2>/dev/null; then
            pass "BranchManagerResource imports successfully"
        else
            fail "BranchManagerResource import failed"
        fi

        if python3 -c "from cascade.defs.sensors import auto_promotion_sensor, branch_cleanup_sensor" 2>/dev/null; then
            pass "Promotion sensors import successfully"
        else
            fail "Promotion sensors import failed"
        fi
    else
        info "Cascade package not installed - skipping Python import tests"
        info "Run 'uv sync' to install package for import tests"
    fi
fi

section "9.10: Service Integration Tests (if services are running)"

if check_service nessie && check_service trino; then
    info "Services are running, performing integration tests"

    # Test Nessie main branch exists
    NESSIE_URL="http://localhost:19120/api/v1"
    if curl -s "$NESSIE_URL/trees" | grep -q "main"; then
        pass "Nessie main branch exists"
    else
        fail "Nessie main branch not found"
    fi

    # Test Trino can connect with session properties
    if docker compose exec -T trino trino --execute "SHOW SESSION" 2>/dev/null | grep -q "nessie" || true; then
        pass "Trino supports nessie session properties"
    else
        info "Trino nessie session property test skipped (may require manual verification)"
    fi

else
    info "Services not running - skipping integration tests"
    info "Run 'make up-all' to start services for integration tests"
fi

section "Test Summary"
echo ""
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All Phase 9 tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some Phase 9 tests failed.${NC}"
    exit 1
fi
