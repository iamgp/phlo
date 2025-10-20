# Port Analysis for Cascade Services

| Service | External Port | Internal Port | Default | Status |
|---------|---------------|---------------|---------|--------|
| postgres | ${POSTGRES_PORT} | 5432 | 5432 | ✅ Unique |
| minio-api | ${MINIO_API_PORT} | 9000 | 9000 | ✅ Unique |
| minio-console | ${MINIO_CONSOLE_PORT} | 9001 | 9001 | ✅ Unique |
| nessie | ${NESSIE_PORT} | 19120 | 19120 | ✅ Unique |
| trino | ${TRINO_PORT} | 8080 | 8080 | ✅ Unique |
| dagster | ${DAGSTER_PORT} | 3000 | 3000 | ✅ Unique |
| superset | ${SUPERSET_PORT} | 8088 | 8088 | ✅ Unique |
| pgweb | ${PGWEB_PORT} | 8081 | 8082 | ✅ Unique |
| hub | ${APP_PORT} | 54321 | 54321 | ✅ Unique |
| prometheus | ${PROMETHEUS_PORT} | 9090 | 9090 | ✅ Unique |
| loki | ${LOKI_PORT} | 3100 | 3100 | ✅ Unique |
| alloy | ${ALLOY_PORT} | 12345 | 12345 | ✅ Unique |
| grafana | ${GRAFANA_PORT} | 3000 | 3001 | ✅ Unique |
| postgres-exporter | ${POSTGRES_EXPORTER_PORT} | 9187 | 9187 | ✅ Unique |
| api | ${API_PORT} | 8000 | 8000 | ✅ Unique |
| hasura | ${HASURA_PORT} | 8080 | 8081 | ✅ Unique |
| mkdocs | ${MKDOCS_PORT} | 8000 | 8001 | ✅ Unique |

## Summary
- **17 services** with unique external ports
- **No port conflicts** detected
- All services use configurable environment variables
- Internal ports are properly mapped to external ports
