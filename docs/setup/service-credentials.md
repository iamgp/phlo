# Service Credentials for Regulated Deployments

In regulated mode, each service should connect to backends with its own scoped
credentials instead of shared admin credentials. This limits blast radius,
enables per-service audit attribution, and satisfies separation-of-duty
requirements.

## What this changes operationally

Before this regulated-mode work, several Phlo services could share backend
identities even when the front door was authenticated. That made it hard to
answer basic audit questions such as "was this change executed by Dagster or by
phlo-api?".

The current regulated posture expects:

- `phlo-api`, Dagster webserver, and Dagster daemon to authenticate separately
  when they call downstream systems
- backend logs to show the service identity that actually performed the action
- write-capable services to carry only the privileges they need

If you enable `regulated: true` but keep broad shared backend credentials, you
have only a partial deployment of the model documented in this PR.

## Why scoped credentials matter

By default, Phlo services share credentials:

- Dagster and phlo-api both use `POSTGRES_USER=phlo` with full privileges
- Dagster uses `MINIO_ROOT_USER` with root access to all buckets
- All services connect to Trino anonymously or with a shared user

In a regulated deployment, this means:

- **No attribution**: Trino/Postgres audit logs can't distinguish phlo-api
  reads from Dagster writes
- **No least-privilege**: phlo-api has write access it doesn't need
- **No blast radius control**: a compromised service token grants full access

## Service role model

| Service | Backend | Role name | Permissions |
|---------|---------|-----------|-------------|
| phlo-api | Trino | `phlo_api_reader` | SELECT on `iceberg.{bronze,silver,gold}.*` |
| phlo-api | PostgreSQL | `phlo_api_service` | SELECT/INSERT/UPDATE on `public.*` |
| dagster | Trino | `phlo_dagster_writer` | SELECT/INSERT/CREATE TABLE on workflow schemas |
| dagster | PostgreSQL | `phlo_dagster_service` | ALL on `public.*` (Dagster storage) |
| dagster | MinIO | `phlo-dagster` policy | Read/write on `lake` bucket |
| hasura | PostgreSQL | `phlo_hasura_readonly` | SELECT only (regulated mode default) |
| postgrest | PostgreSQL | `phlo_postgrest_readonly` | SELECT only (regulated mode default) |

## Step 1: Create backend roles

### Trino and PostgreSQL

Run the provided SQL script against your backends:

```bash
# PostgreSQL roles (run as superuser)
psql -U postgres -d phlo -f scripts/create-service-roles.sql

# Trino roles (run as admin via trino-cli)
trino --execute "$(grep -A999 'Trino roles' scripts/create-service-roles.sql | grep -B999 'PostgreSQL roles' | grep -v '^--')"
```

> **Important:** Change the placeholder passwords (`changeme_*`) to strong
> secrets before running. Store them in `.phlo/.env.local`.

### MinIO

Run the MinIO policy creation script:

```bash
# Set up MinIO alias first
mc alias set phlo http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

# Create scoped policies and service accounts
./scripts/create-minio-service-policies.sh
```

## Step 2: Configure `.phlo/.env.local`

Add scoped credentials for each service:

```env
# Dagster service credentials
DAGSTER_POSTGRES_USER=phlo_dagster_service
DAGSTER_POSTGRES_PASSWORD=<your-dagster-postgres-password>
DAGSTER_TRINO_USER=phlo-dagster
DAGSTER_TRINO_ROLE=phlo_dagster_writer
DAGSTER_MINIO_ACCESS_KEY=phlo-dagster-svc
DAGSTER_MINIO_SECRET_KEY=<your-dagster-minio-secret>

# phlo-api service credentials
PHLO_API_TRINO_USER=phlo-api
PHLO_API_TRINO_ROLE=phlo_api_reader

# Service-to-service auth secret
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
PHLO_SERVICE_SECRET=<your-service-secret>
```

## Step 3: Restart services

```bash
phlo services stop
phlo services start
```

## Step 4: Verify

Check that each service connects with its scoped role:

```bash
# Verify Dagster Postgres connection
docker exec dagster-webserver psql -U phlo_dagster_service -d phlo -c "SELECT current_user;"

# Verify phlo-api Trino connection
# In Observatory, run a query and check Trino query logs for user=phlo-api
phlo services logs -f trino | grep "phlo-api"
```

## Backward compatibility

All scoped credential env vars fall back to the shared defaults when unset:

- `DAGSTER_POSTGRES_USER` → `POSTGRES_USER` → `phlo`
- `DAGSTER_MINIO_ACCESS_KEY` → `MINIO_ROOT_USER` → `minio`
- `PHLO_API_TRINO_USER` → `phlo-api` (default, no admin fallback)

Development setups continue to work without any new env vars.

That fallback exists to preserve local development and upgrades. It should not
be treated as the target state for a regulated deployment.

## Hasura / PostgREST in regulated mode

In regulated mode, Hasura and PostgREST are write-restricted by default.
The SQL script creates read-only roles for both. To enable writes, set
`surfaces.<service>.allow_writes: true` in `phlo.yaml` and use a role
with appropriate permissions.

See [API Surfaces](../reference/api-surfaces.md) for the write restriction
policy.
