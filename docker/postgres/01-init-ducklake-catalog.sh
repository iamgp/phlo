#!/bin/bash
set -e

# Create ducklake_catalog database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE ducklake_catalog'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ducklake_catalog')\gexec
EOSQL

echo "ducklake_catalog database ensured"
