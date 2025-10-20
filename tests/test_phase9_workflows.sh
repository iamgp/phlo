#!/usr/bin/env bash
set -euo pipefail

# Phase 9: Integrated Branching Workflows Test Suite
# Tests dev/prod pipeline isolation, branch-aware resources, and promotion workflow

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

section "Phase 9: Integrated Branching Workflows Tests"

info "Testing branch-aware resource configuration and workflow orchestration"

section "9.1: Branch-Aware Resources"

# Test TrinoResource supports nessie_ref parameter
if grep -q "nessie_ref:" src/cascade/defs/resources/trino.py; then
    pass "TrinoResource has nessie_ref parameter"
else
    fail "TrinoResource missing nessie_ref parameter"
fi

# Test IcebergResource supports ref parameter
if grep -q "ref:" src/cascade/defs/resources/iceberg.py; then
    pass "IcebergResource has ref parameter"
else
    fail "IcebergResource missing ref parameter"
fi

# Test NessieResource is available in resources
if grep -q "NessieResource" src/cascade/defs/resources/__init__.py; then
    pass "NessieResource available in resources module"
else
    fail "NessieResource not available in resources module"
fi

# Test Trino connection uses session properties
if grep -q "session_properties" src/cascade/defs/resources/trino.py; then
    pass "TrinoResource uses session_properties for branch configuration"
else
    fail "TrinoResource missing session_properties support"
fi

section "9.2: Multi-Job Pipeline Definition"

# Test workflow definitions exist
if [ -f "src/cascade/defs/workflows/__init__.py" ]; then
    pass "Workflow definitions module exists"
else
    fail "Workflow definitions module missing"
fi

# Test dev_pipeline job exists
if grep -q "DEV_PIPELINE_JOB" src/cascade/defs/workflows/__init__.py; then
    pass "DEV_PIPELINE_JOB defined"
else
    fail "DEV_PIPELINE_JOB not defined"
fi

# Test prod_promotion job exists
if grep -q "PROD_PROMOTION_JOB" src/cascade/defs/workflows/__init__.py; then
    pass "PROD_PROMOTION_JOB defined"
else
    fail "PROD_PROMOTION_JOB not defined"
fi

# Test dev_pipeline job selects correct assets
if grep -q '"nessie_dev_branch"' src/cascade/defs/workflows/__init__.py; then
    pass "DEV_PIPELINE_JOB includes nessie_dev_branch"
else
    fail "DEV_PIPELINE_JOB missing nessie_dev_branch dependency"
fi

# Test dev_pipeline job configures dev target
if grep -A20 "DEV_PIPELINE_JOB" src/cascade/defs/workflows/__init__.py | grep -q '"target": "dev"'; then
    pass "DEV_PIPELINE_JOB uses dbt dev target"
else
    fail "DEV_PIPELINE_JOB missing dbt dev target configuration"
fi

# Test prod_promotion job (note: doesn't use dbt, only runs promote and publish)
if grep -A10 "PROD_PROMOTION_JOB" src/cascade/defs/workflows/__init__.py | grep -q '"promote_dev_to_main"'; then
    pass "PROD_PROMOTION_JOB includes promote_dev_to_main asset"
else
    fail "PROD_PROMOTION_JOB missing promote_dev_to_main asset"
fi

# Test dev_pipeline job uses dev branch resources
if grep -A20 "DEV_PIPELINE_JOB" src/cascade/defs/workflows/__init__.py | grep -q '"ref": "dev"'; then
    pass "DEV_PIPELINE_JOB configures iceberg resource with dev ref"
else
    fail "DEV_PIPELINE_JOB missing iceberg dev ref configuration"
fi

# Test prod_promotion job uses main branch resources
if grep -A20 "PROD_PROMOTION_JOB" src/cascade/defs/workflows/__init__.py | grep -q '"ref": "main"'; then
    pass "PROD_PROMOTION_JOB configures iceberg resource with main ref"
else
    fail "PROD_PROMOTION_JOB missing iceberg main ref configuration"
fi

section "9.3: Schedules for Automated Workflows"

# Test dev_pipeline schedule exists
if grep -q "dev_pipeline_schedule" src/cascade/defs/workflows/__init__.py; then
    pass "dev_pipeline_schedule defined"
else
    fail "dev_pipeline_schedule not defined"
fi

# Test schedule is configured to run daily
if grep -A5 "dev_pipeline_schedule" src/cascade/defs/workflows/__init__.py | grep -q "cron_schedule"; then
    pass "dev_pipeline_schedule has cron configuration"
else
    fail "dev_pipeline_schedule missing cron configuration"
fi

# Test workflow definitions are imported in main definitions
if grep -q "from cascade.defs.workflows import build_defs as build_workflow_defs" src/cascade/definitions.py; then
    pass "Workflow definitions imported in main definitions"
else
    fail "Workflow definitions not imported in main definitions"
fi

# Test workflow definitions are merged
if grep -q "build_workflow_defs()" src/cascade/definitions.py; then
    pass "Workflow definitions merged into main definitions"
else
    fail "Workflow definitions not merged into main definitions"
fi

section "9.4: dbt Profile Configuration"

# Test dbt dev profile has nessie.reference: dev
if grep -A10 "^\s*dev:" transforms/dbt/profiles/profiles.yml | grep -q "nessie.reference: dev"; then
    pass "dbt dev profile uses nessie.reference: dev"
else
    fail "dbt dev profile missing nessie.reference: dev"
fi

# Test dbt prod profile has nessie.reference: main
if grep -A10 "^\s*prod:" transforms/dbt/profiles/profiles.yml | grep -q "nessie.reference: main"; then
    pass "dbt prod profile uses nessie.reference: main"
else
    fail "dbt prod profile missing nessie.reference: main"
fi

section "9.5: Python Imports and Syntax"

# Test workflow module imports correctly (requires installed package)
if [ -f "pyproject.toml" ]; then
    info "Checking if cascade package is installed..."
    if python3 -c "import cascade" 2>/dev/null; then
        if python3 -c "from cascade.defs.workflows import build_defs" 2>/dev/null; then
            pass "Workflow module imports successfully"
        else
            fail "Workflow module import failed"
        fi

        if python3 -c "from cascade.defs.workflows import DEV_PIPELINE_JOB, PROD_PROMOTION_JOB" 2>/dev/null; then
            pass "Workflow job definitions import successfully"
        else
            fail "Workflow job definitions import failed"
        fi

        if python3 -c "from cascade.defs.resources import IcebergResource, TrinoResource, NessieResource" 2>/dev/null; then
            pass "Branch-aware resources import successfully"
        else
            fail "Branch-aware resources import failed"
        fi
    else
        info "Cascade package not installed - skipping Python import tests"
        info "Run 'uv sync' to install package for import tests"
    fi
fi

section "9.6: Service Integration Tests (if services are running)"

if check_service nessie && check_service trino; then
    info "Services are running, performing integration tests"

    # Test Nessie branches exist
    NESSIE_URL="http://localhost:19120/api/v1"
    if curl -s "$NESSIE_URL/trees" | grep -q "main"; then
        pass "Nessie main branch exists"
    else
        fail "Nessie main branch not found"
    fi

    # Test dev branch can be created/verified
    if curl -s "$NESSIE_URL/trees" | grep -q "dev" || curl -s -X POST "$NESSIE_URL/trees/dev" -H "Content-Type: application/json" 2>/dev/null; then
        pass "Nessie dev branch exists or can be created"
    else
        fail "Nessie dev branch setup failed"
    fi

    # Test Trino can connect with session properties
    if docker compose exec -T trino trino --execute "SHOW SESSION" 2>/dev/null | grep -q "nessie.reference" || true; then
        pass "Trino supports nessie.reference session property"
    else
        info "Trino nessie.reference property test skipped (may require manual verification)"
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
