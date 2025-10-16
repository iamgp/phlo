#!/usr/bin/env bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run database migrations
echo "Running database migrations..."
superset db upgrade

# Create admin user if it doesn't exist
echo "Creating admin user..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname Admin \
  --lastname User \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin123}" 2>/dev/null || echo "Admin user already exists"

# Initialize Superset
echo "Initializing Superset..."
superset init

echo "Superset initialization complete!"
