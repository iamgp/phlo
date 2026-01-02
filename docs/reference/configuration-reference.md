# Configuration Reference

Complete reference for configuring Phlo.

## Configuration System

Phlo uses multiple configuration sources:

1. **Infrastructure defaults** (`phlo.yaml`, `env:`)
2. **Local secrets/overrides** (`.phlo/.env.local`)
3. **Runtime environment** (process environment variables)
4. **Python settings** (`phlo.config`)
5. **Runtime configuration** (Dagster run config)

## Environment Variables

Environment variables are materialized into `.phlo/.env` (generated, non-secret defaults)
and `.phlo/.env.local` (local secrets). Edit `phlo.yaml` for committed defaults and
`.phlo/.env.local` for secrets.

### Database Configuration

PostgreSQL database settings:

```bash
# Host and port
POSTGRES_HOST=postgres
POSTGRES_PORT=10000

# Credentials
POSTGRES_USER=lake
POSTGRES_PASSWORD=phlo

# Database
POSTGRES_DB=lakehouse
POSTGRES_MART_SCHEMA=marts

# Lineage tracking database (optional, defaults to Dagster Postgres connection)
PHLO_LINEAGE_DB_URL=postgresql://lake:phlo@postgres:10000/lakehouse
# Alternative: DAGSTER_PG_DB_CONNECTION_STRING (alias for lineage_db_url)
```

**Connection string format**:

```
postgresql://lake:phlo@postgres:10000/lakehouse
```

### Storage Configuration

MinIO S3-compatible object storage:

```bash
# Host and ports
MINIO_HOST=minio
MINIO_API_PORT=10001
MINIO_CONSOLE_PORT=10002

# Credentials
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

**MinIO endpoint**:

```
http://minio:10001
```

**Console UI**: http://localhost:10002

### Catalog Configuration

Nessie Git-like catalog:

```bash
# Version and connectivity
NESSIE_VERSION=0.106.0
NESSIE_PORT=19120
NESSIE_HOST=nessie
NESSIE_API_VERSION=v1
```

**API endpoints**:

- v1 API: `http://nessie:10003/api/v1`
- v2 API: `http://nessie:10003/api/v2`
- Iceberg REST: `http://nessie:10003/iceberg`

### Query Engine Configuration

Trino distributed SQL engine:

```bash
# Version and connectivity
TRINO_VERSION=477
TRINO_PORT=10005
TRINO_HOST=trino

# Catalog
TRINO_CATALOG=iceberg
```

**Connection string**:

```
trino://trino:10005/iceberg_dev
```

### Data Lake Configuration

Apache Iceberg table format:

```bash
# Storage paths
ICEBERG_WAREHOUSE_PATH=s3://lake/warehouse
ICEBERG_STAGING_PATH=s3://lake/stage

# Default namespace
ICEBERG_DEFAULT_NAMESPACE=raw

# Default branch reference
ICEBERG_NESSIE_REF=main
```

**Warehouse paths by branch**:

```python
# main branch
s3://lake/warehouse

# Custom branch
s3://lake/warehouse@feature-branch
```

### Branch Management

Nessie branch lifecycle configuration:

```bash
# Retention periods (days)
BRANCH_RETENTION_DAYS=7
BRANCH_RETENTION_DAYS_FAILED=2

# Automation
AUTO_PROMOTE_ENABLED=true
BRANCH_CLEANUP_ENABLED=false
```

**Behavior**:

- `BRANCH_RETENTION_DAYS`: Days to keep successful pipeline branches
- `BRANCH_RETENTION_DAYS_FAILED`: Days to keep failed pipeline branches
- `AUTO_PROMOTE_ENABLED`: Auto-merge to main when quality checks pass
- `BRANCH_CLEANUP_ENABLED`: Automatically delete old branches

### Validation Configuration

Data quality validation settings:

```bash
# Freshness blocking
FRESHNESS_BLOCKS_PROMOTION=false

# Pandera validation level
PANDERA_CRITICAL_LEVEL=error  # error, warning, or skip

# Validation retry
VALIDATION_RETRY_ENABLED=true
VALIDATION_RETRY_MAX_ATTEMPTS=3
VALIDATION_RETRY_DELAY_SECONDS=300  # seconds
```

**Pandera levels**:

- `error`: Validation failures block pipeline
- `warning`: Log warnings but continue
- `skip`: Skip validation entirely (not recommended)

### Service Configuration

#### Superset

Business intelligence and visualization:

```bash
SUPERSET_PORT=10007
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@superset.com
```

Access: http://localhost:10007

#### Dagster

Orchestration platform:

```bash
DAGSTER_PORT=10006

# Executor configuration (set only one)
PHLO_FORCE_IN_PROCESS_EXECUTOR=false   # Force in-process executor
PHLO_FORCE_MULTIPROCESS_EXECUTOR=false # Force multiprocess executor

# Host platform (auto-detected, but can be set explicitly for daemon/webserver on macOS)
PHLO_HOST_PLATFORM=  # Darwin, Linux, or Windows
```

Access: http://localhost:10006

#### Hub/Flask

Internal API server:

```bash
HUB_APP_PORT=10009
HUB_DEBUG=false
```

### Integration Services

#### API Layer

JWT authentication:

```bash
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

#### Hasura GraphQL

```bash
HASURA_GRAPHQL_PORT=10012
HASURA_GRAPHQL_ADMIN_SECRET=hasura-admin-secret
HASURA_GRAPHQL_ENABLE_CONSOLE=true
```

Access: http://localhost:10012

#### PostgREST

```bash
POSTGREST_PORT=10011
POSTGREST_DB_SCHEMA=marts
POSTGREST_DB_ANON_ROLE=web_anon
```

Access: http://localhost:10011

#### OpenMetadata

Data catalog and governance:

```bash
OPENMETADATA_HOST=openmetadata-server
OPENMETADATA_PORT=8585
OPENMETADATA_USERNAME=admin
OPENMETADATA_PASSWORD=admin
OPENMETADATA_VERIFY_SSL=false
OPENMETADATA_SYNC_ENABLED=true
OPENMETADATA_SYNC_INTERVAL_SECONDS=300  # Minimum interval between syncs
```

Access: http://localhost:8585

### Observability Stack

#### Prometheus

Metrics collection:

```bash
PROMETHEUS_PORT=9090
```

Access: http://localhost:9090

#### Loki

Log aggregation:

```bash
LOKI_PORT=3100
```

#### Grafana

Dashboards and visualization:

```bash
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

Access: http://localhost:3000

### Alerting Configuration

#### Slack

```bash
PHLO_ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PHLO_ALERT_SLACK_CHANNEL=#data-alerts
```

#### PagerDuty

```bash
PHLO_ALERT_PAGERDUTY_KEY=your-integration-key
```

#### Email (SMTP)

```bash
PHLO_ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
PHLO_ALERT_EMAIL_SMTP_PORT=587
PHLO_ALERT_EMAIL_SMTP_USER=your-email@gmail.com
PHLO_ALERT_EMAIL_SMTP_PASSWORD=your-app-password
PHLO_ALERT_EMAIL_RECIPIENTS=team@yourdomain.com,alerts@yourdomain.com  # Comma-separated list
```

### Security Configuration

See [Security Setup Guide](../setup/security.md) for detailed setup instructions.

#### Trino Authentication

```bash
# Authentication type (PASSWORD, OAUTH2, JWT, CERTIFICATE, KERBEROS, or empty)
TRINO_AUTH_TYPE=

# LDAP Authentication (when TRINO_AUTH_TYPE=PASSWORD)
TRINO_LDAP_URL=ldaps://ldap.example.com:636
TRINO_LDAP_USER_BIND_PATTERN=${USER}@example.com

# OAuth2/OIDC Authentication (when TRINO_AUTH_TYPE=OAUTH2)
TRINO_OAUTH2_ISSUER=https://auth.example.com
TRINO_OAUTH2_CLIENT_ID=trino
TRINO_OAUTH2_CLIENT_SECRET=your-client-secret

# HTTPS/TLS
TRINO_HTTPS_ENABLED=false
TRINO_HTTPS_KEYSTORE_PATH=/etc/trino/keystore.jks
TRINO_HTTPS_KEYSTORE_PASSWORD=keystore-password

# Access Control
TRINO_ACCESS_CONTROL_TYPE=file
TRINO_ACCESS_CONTROL_CONFIG_FILE=/etc/trino/access-control.json
```

#### Nessie Authentication

```bash
# OIDC/OAuth2 Authentication
NESSIE_OIDC_ENABLED=false
NESSIE_OIDC_SERVER_URL=https://auth.example.com/realms/phlo
NESSIE_OIDC_CLIENT_ID=nessie
NESSIE_OIDC_CLIENT_SECRET=your-client-secret
NESSIE_OIDC_ISSUER=https://auth.example.com

# Authorization
NESSIE_AUTHZ_ENABLED=false
```

#### MinIO Security

```bash
# TLS (set server URL to enable HTTPS)
MINIO_SERVER_URL=https://minio.example.com

# OIDC Authentication
MINIO_OIDC_CONFIG_URL=https://auth.example.com/.well-known/openid-configuration
MINIO_OIDC_CLIENT_ID=minio
MINIO_OIDC_CLIENT_SECRET=your-client-secret
MINIO_OIDC_CLAIM_NAME=policy
MINIO_OIDC_SCOPES=openid

# LDAP Authentication
MINIO_LDAP_SERVER=ldap.example.com:636
MINIO_LDAP_BIND_DN=cn=admin,dc=example,dc=com
MINIO_LDAP_BIND_PASSWORD=ldap-password
MINIO_LDAP_USER_BASE_DN=ou=users,dc=example,dc=com
MINIO_LDAP_USER_FILTER=(uid=%s)

# Encryption at Rest
MINIO_AUTO_ENCRYPTION=off

# Audit Logging
MINIO_AUDIT_ENABLED=off
MINIO_AUDIT_ENDPOINT=http://audit-service:8080/logs
```

#### PostgreSQL SSL

```bash
# SSL Mode (disable, allow, prefer, require, verify-ca, verify-full)
POSTGRES_SSL_MODE=prefer
POSTGRES_SSL_CERT_FILE=/path/to/cert.pem
POSTGRES_SSL_KEY_FILE=/path/to/key.pem
POSTGRES_SSL_CA_FILE=/path/to/ca.pem
```

### dbt Configuration

```bash
# dbt artifact paths (defaults to <DBT_PROJECT_DIR>/target when unset)
DBT_MANIFEST_PATH=workflows/transforms/dbt/target/manifest.json
DBT_CATALOG_PATH=workflows/transforms/dbt/target/catalog.json

# dbt project directory
DBT_PROJECT_DIR=workflows/transforms/dbt

# Workflows path (for external projects)
WORKFLOWS_PATH=workflows
```

### Plugin Configuration

```bash
# Plugin system
PLUGINS_ENABLED=true
PLUGINS_AUTO_DISCOVER=true

# Whitelist/blacklist (comma-separated)
PLUGINS_WHITELIST=plugin1,plugin2
PLUGINS_BLACKLIST=deprecated_plugin

# Plugin registry
PLUGIN_REGISTRY_URL=https://registry.phlo.dev/plugins.json
PLUGIN_REGISTRY_CACHE_TTL_SECONDS=3600
PLUGIN_REGISTRY_TIMEOUT_SECONDS=10
```

## Infrastructure Configuration (phlo.yaml)

Project-level configuration in `phlo.yaml`:

```yaml
name: my-project
description: My data lakehouse project

infrastructure:
  # Container naming pattern
  container_naming_pattern: "{{project}}-{{service}}-1"

  # Service-specific configuration
  services:
    dagster_webserver:
      container_name: null # Use pattern
      service_name: dagster-webserver
      host: localhost
      internal_host: dagster-webserver
      port: 10006

    postgres:
      container_name: null
      service_name: postgres
      host: localhost
      internal_host: postgres
      port: 10000
      credentials:
        user: postgres
        password: postgres
        database: cascade

    minio:
      container_name: null
      service_name: minio
      host: localhost
      internal_host: minio
      api_port: 10001
      console_port: 10002

    nessie:
      container_name: null
      service_name: nessie
      host: localhost
      internal_host: nessie
      port: 10003

    trino:
      container_name: null
      service_name: trino
      host: localhost
      internal_host: trino
      port: 10005
```

### Loading Infrastructure Config

```python
from phlo.infrastructure.config import (
    load_infrastructure_config,
    get_container_name,
    get_service_config
)

# Load config
config = load_infrastructure_config()

# Get container name
container = get_container_name("dagster-webserver")
# Returns: "my-project-dagster-webserver-1"

# Get service config
service = get_service_config("postgres")
# Returns: dict with host, port, credentials, etc.
```

## Python Configuration (config.py)

Programmatic access to configuration:

```python
from phlo.config import settings

# Database
settings.postgres_host
settings.postgres_port
settings.get_postgres_connection_string()

# MinIO
settings.minio_endpoint
# Returns: "http://minio:10001"

# Nessie
settings.nessie_uri
settings.nessie_api_v1_uri
settings.nessie_iceberg_rest_uri

# Trino
settings.trino_connection_string
# Returns: "trino://trino:10005/iceberg_dev"

# Iceberg
settings.iceberg_warehouse_path
settings.get_iceberg_warehouse_for_branch("main")
# Returns: "s3://lake/warehouse"

settings.get_iceberg_warehouse_for_branch("feature")
# Returns: "s3://lake/warehouse@feature"
```

## Runtime Configuration

Dagster run configuration for asset execution:

```python
# Example run config
{
    "ops": {
        "my_asset": {
            "config": {
                "partition_date": "2025-01-15",
                "full_refresh": false
            }
        }
    },
    "resources": {
        "iceberg": {
            "config": {
                "ref": "pipeline/run-abc123"
            }
        }
    }
}
```

## Port Reference

Standard port assignments:

```
10000  PostgreSQL
10001  MinIO API
10002  MinIO Console
10003  Nessie
10005  Trino
10006  Dagster
10007  Superset
10009  Hub/Flask
10011  PostgREST
10012  Hasura GraphQL
8585   OpenMetadata
3000   Grafana
9090   Prometheus
3100   Loki
```

## Environment-Specific Configurations

### Development

```yaml
# phlo.yaml (development)
env:
  POSTGRES_HOST: localhost
  MINIO_HOST: localhost
  DAGSTER_HOST_PLATFORM: local
  HUB_DEBUG: true
  AUTO_PROMOTE_ENABLED: true
  BRANCH_CLEANUP_ENABLED: false
```

### Staging

```yaml
# phlo.staging.yaml
env:
  POSTGRES_HOST: postgres-staging
  MINIO_HOST: minio-staging
  DAGSTER_HOST_PLATFORM: docker
  HUB_DEBUG: false
  AUTO_PROMOTE_ENABLED: true
  BRANCH_CLEANUP_ENABLED: true
  BRANCH_RETENTION_DAYS: 3
```

### Production

```yaml
# phlo.production.yaml
env:
  POSTGRES_HOST: postgres-prod.internal
  POSTGRES_PORT: 5432
  MINIO_HOST: minio-prod.internal
  NESSIE_HOST: nessie-prod.internal
  TRINO_HOST: trino-prod.internal
  DAGSTER_HOST_PLATFORM: k8s
  DAGSTER_EXECUTOR: multiprocess
  HUB_DEBUG: false
  AUTO_PROMOTE_ENABLED: true
  BRANCH_CLEANUP_ENABLED: true
  BRANCH_RETENTION_DAYS: 7
  BRANCH_RETENTION_DAYS_FAILED: 2
  FRESHNESS_BLOCKS_PROMOTION: true
  PANDERA_CRITICAL_LEVEL: error
  VALIDATION_RETRY_ENABLED: true
  OPENMETADATA_SYNC_ENABLED: true
```

## Security Best Practices

### Secrets Management

Do not commit secrets to version control:

```bash
# .gitignore
.phlo/.env.local
```

Use environment-specific files:

```bash
.env.example      # Secrets template (committed)
.phlo/.env.local  # Local secrets (ignored)
```

### Strong Passwords

Generate secure passwords:

```bash
# Generate random password
openssl rand -base64 32

# Use in .phlo/.env.local
POSTGRES_PASSWORD=<generated-password>
MINIO_ROOT_PASSWORD=<generated-password>
JWT_SECRET_KEY=<generated-password>
```

### Minimal Permissions

Use least-privilege principle:

```bash
# Read-only user for BI tools
POSTGRES_BI_USER=bi_readonly
POSTGRES_BI_PASSWORD=<password>

# Grant only SELECT on marts
GRANT SELECT ON SCHEMA marts TO bi_readonly;
```

## Configuration Validation

### Validate with CLI

```bash
# Validate phlo.yaml
phlo config validate phlo.yaml

# Show current config
phlo config show

# Show with secrets (masked by default)
phlo config show --secrets
```

### Validation in Python

```python
from phlo.config import settings
from pydantic import ValidationError

try:
    # Access settings (validates on load)
    conn_str = settings.get_postgres_connection_string()
except ValidationError as e:
    print(f"Configuration error: {e}")
```

## Troubleshooting

### Connection Issues

```bash
# Test PostgreSQL
psql postgresql://postgres:password@localhost:10000/cascade

# Test MinIO
mc alias set local http://localhost:10001 minioadmin minioadmin
mc ls local

# Test Nessie
curl http://localhost:10003/api/v2/config

# Test Trino
docker exec -it phlo-trino-1 trino
```

### Port Conflicts

Check if ports are in use:

```bash
# macOS/Linux
lsof -i :10000
lsof -i :10006

# Windows
netstat -ano | findstr :10000
```

Change ports in `phlo.yaml` (env:):

```bash
POSTGRES_PORT=15432
DAGSTER_PORT=13000
```

### Permission Errors

Fix Docker volume permissions:

```bash
sudo chown -R $USER:$USER .phlo/
chmod -R 755 .phlo/
```

## Next Steps

- [Installation Guide](../getting-started/installation.md) - Setup instructions
- [CLI Reference](cli-reference.md) - Command-line tools
- [Developer Guide](../guides/developer-guide.md) - Building workflows
- [Troubleshooting](../operations/troubleshooting.md) - Common issues
