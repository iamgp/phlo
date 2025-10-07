#!/usr/bin/env bash
set -e
superset fab create-admin \
  --username ${SUPERSET_ADMIN_USER:-admin} \
  --firstname Admin --lastname User \
  --email ${SUPERSET_ADMIN_EMAIL:-admin@example.com} \
  --password ${SUPERSET_ADMIN_PASSWORD:-admin123} || true
superset db upgrade
superset init
