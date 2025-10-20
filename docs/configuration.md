# Configuration Guide

Cascade uses environment variables for configuration, centralized through Pydantic settings in `cascade/config.py`.

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

### Database Configuration

```bash
# PostgreSQL settings
POSTGRES_USER=lake
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=lakehouse
POSTGRES_PORT=10000
```

### Object Storage (MinIO)

```bash
# MinIO settings
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=your_secure_password
MINIO_API_PORT=10001
MINIO_CONSOLE_PORT=10002
```

### Data Catalog (Nessie)

```bash
# Nessie settings
NESSIE_VERSION=0.105.5
NESSIE_PORT=10003
```

### Query Engine (Trino)

```bash
# Trino settings
TRINO_VERSION=477
TRINO_PORT=10005
```

### Orchestration (Dagster)

```bash
# Dagster settings
DAGSTER_PORT=10006
```

### Business Intelligence (Superset)

```bash
# Superset settings
SUPERSET_PORT=10007
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=your_secure_password
SUPERSET_ADMIN_EMAIL=admin@example.com
```

### Documentation (MkDocs)

```bash
# MkDocs settings
MKDOCS_PORT=10012
```

### API Layer

```bash
# FastAPI settings
API_PORT=10010
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Hasura GraphQL settings
HASURA_PORT=10011
HASURA_ADMIN_SECRET=your_admin_secret
```

### Observability

```bash
# Prometheus, Grafana, Loki settings
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
LOKI_PORT=3100
```

## Service Profiles

Cascade uses Docker Compose profiles to start services in logical groups:

- **core**: PostgreSQL, MinIO, Dagster, Hub (required)
- **query**: Trino, Nessie (required for analytics)
- **bi**: Superset, pgweb (optional)
- **docs**: MkDocs (optional)
- **api**: FastAPI, Hasura (optional)
- **observability**: Prometheus, Grafana, Loki, Alloy (optional)
- **all**: All services

## Configuration Classes

The `cascade.config` module provides typed configuration:

```python
from cascade.config import config

# Access configuration
print(config.postgres.host)
print(config.minio.root_user)
print(config.dagster.port)
```

## Security Considerations

- Change all default passwords in production
- Use strong, unique passwords for each service
- Consider using Docker secrets for sensitive values
- Rotate JWT secrets regularly
- Use HTTPS in production environments

## Development vs Production

For development:
- Use default ports and localhost endpoints
- Enable debug logging
- Use minimal resource allocation

For production:
- Use secure passwords and secrets management
- Configure proper networking and firewalls
- Set up monitoring and alerting
- Use production-grade storage volumes
- Configure backup and recovery procedures
