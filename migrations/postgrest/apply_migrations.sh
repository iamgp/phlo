#!/bin/bash
# Apply PostgREST migrations to PostgreSQL database

set -e  # Exit on error

# Database connection settings
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-10000}"
DB_NAME="${DB_NAME:-lakehouse}"
DB_USER="${DB_USER:-lake}"
DB_PASSWORD="${DB_PASSWORD:-lakepass}"

# PGPASSWORD for non-interactive execution
export PGPASSWORD="$DB_PASSWORD"

echo "======================================"
echo "PostgREST Database Migration"
echo "======================================"
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "======================================"
echo ""

# Function to run SQL file
run_migration() {
  local file=$1
  echo "Running: $file"
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
  if [ $? -eq 0 ]; then
    echo "✓ $file completed successfully"
    echo ""
  else
    echo "✗ $file failed"
    exit 1
  fi
}

# Run migrations in order
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_migration "$SCRIPT_DIR/001_extensions.sql"
run_migration "$SCRIPT_DIR/002_auth_schema.sql"
run_migration "$SCRIPT_DIR/003_jwt_functions.sql"
run_migration "$SCRIPT_DIR/004_api_schema.sql"
run_migration "$SCRIPT_DIR/005_api_functions.sql"
run_migration "$SCRIPT_DIR/006_roles_and_rls.sql"

echo "======================================"
echo "✓ All migrations completed successfully!"
echo "======================================"
echo ""
echo "Test the setup with:"
echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \"SELECT api.login('analyst', 'analyst123');\""
