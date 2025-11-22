# PostgREST Database Migrations

This directory contains PostgreSQL migrations for the PostgREST API implementation.

## Overview

These migrations transform the Phlo Lakehouse database to support PostgREST, a standalone web server that automatically generates RESTful APIs from PostgreSQL schemas.

## Migration Files

| File | Description |
|------|-------------|
| `001_extensions.sql` | Install required PostgreSQL extensions (pgcrypto) |
| `002_auth_schema.sql` | Create auth schema and users table |
| `003_jwt_functions.sql` | Implement JWT signing and verification functions |
| `004_api_schema.sql` | Create api schema with glucose data views |
| `005_api_functions.sql` | Create API functions (login, statistics, user info) |
| `006_roles_and_rls.sql` | Create PostgreSQL roles and RLS policies |

## Quick Start

### Apply All Migrations

```bash
cd migrations/postgrest
./apply_migrations.sh
```

### Test the API

```bash
./test_postgrest.sh
```

## What Gets Created

### Schemas

- **`auth`**: Private schema for user authentication (not exposed via API)
- **`api`**: Public schema exposed via PostgREST

### Tables

- **`auth.users`**: User accounts with bcrypt-hashed passwords

### Views

- **`api.glucose_readings`**: Daily glucose readings with all metrics
- **`api.glucose_daily_summary`**: Focused daily summary for dashboards
- **`api.glucose_hourly_patterns`**: Time-of-day glucose patterns

### Functions

- **`api.login(username, password)`**: Authenticate and return JWT token
- **`api.glucose_statistics(period_days)`**: Calculate glucose statistics for period
- **`api.user_info()`**: Get current authenticated user information
- **`api.health()`**: Health check endpoint

### Roles

- **`authenticator`**: PostgREST connection role (can switch to other roles)
- **`anon`**: Unauthenticated users
- **`authenticated`**: Base role for authenticated users
- **`analyst`**: Analyst role with read access
- **`admin`**: Administrator role with full access

## Default Users

Two test users are created:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `analyst` | `analyst123` | analyst |

**Important:** Change these passwords in production!

## Database Configuration

The migrations expect:

- **Host:** localhost (or postgres in Docker)
- **Port:** 5432 (internal) / 10000 (external)
- **Database:** lakehouse
- **User:** lake
- **Password:** lakepass

Modify `apply_migrations.sh` if your setup differs.

## Testing

After applying migrations, test with:

```bash
# Test login
psql -h localhost -p 10000 -U lake -d lakehouse -c "
  SELECT api.login('analyst', 'analyst123');
"

# List API views
psql -h localhost -p 10000 -U lake -d lakehouse -c "
  SELECT schemaname, viewname
  FROM pg_views
  WHERE schemaname = 'api';
"

# Test statistics function
psql -h localhost -p 10000 -U lake -d lakehouse -c "
  SELECT api.glucose_statistics(7);
"
```

## Rollback

To rollback migrations (dangerous - destroys data!):

```sql
-- Drop API schema
DROP SCHEMA IF EXISTS api CASCADE;

-- Drop auth schema
DROP SCHEMA IF EXISTS auth CASCADE;

-- Drop roles
DROP ROLE IF EXISTS admin;
DROP ROLE IF EXISTS analyst;
DROP ROLE IF EXISTS authenticated;
DROP ROLE IF EXISTS anon;
DROP ROLE IF EXISTS authenticator;
```

## Next Steps

1. **Deploy PostgREST:** See [docs/POSTGREST_DEPLOYMENT.md](../../docs/POSTGREST_DEPLOYMENT.md)
2. **Test API:** Run `./test_postgrest.sh`
3. **Integrate Clients:** Update applications to use PostgREST endpoints

## Resources

- [PostgREST Documentation](https://postgrest.org)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Migration PRD](../../docs/prd-postgrest-migration.md)

## Support

For issues:
1. Check migration logs
2. Verify PostgreSQL version (12+)
3. Review deployment documentation
4. Open GitHub issue with reproduction steps
