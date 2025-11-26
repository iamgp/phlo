# PostgREST Deployment Guide

This guide covers deploying PostgREST alongside the existing FastAPI service in the Phlo Lakehouse platform.

## Overview

PostgREST is a standalone web server that automatically generates a RESTful API from your PostgreSQL database schema. This deployment implements Phase 1 of the [PostgREST Migration PRD](prd-postgrest-migration.md).

**Key Benefits:**
- Zero-code API generation from database schema
- Auto-generated OpenAPI documentation
- Database-native authentication with JWT
- High performance (written in Haskell)
- Reduced code complexity

---

## Prerequisites

1. **PostgreSQL 12+** with:
   - `pgcrypto` extension (for password hashing)
   - Superuser access (for creating roles and schemas)

2. **Docker Compose** (for containerized deployment)

3. **Phlo services running**:
   - PostgreSQL database
   - (Optional) FastAPI for comparison

---

## Deployment Steps

### Step 1: Update Environment Variables

Copy `.env.example` to `.env` if you haven't already:

```bash
cp .env.example .env
```

Ensure these variables are set in `.env`:

```bash
# PostgREST Configuration
POSTGREST_VERSION=v12.2.3
POSTGREST_PORT=10018
POSTGREST_ADMIN_PORT=10019
POSTGREST_AUTHENTICATOR_PASSWORD=your_secure_password_here

# Shared JWT Secret (must match FastAPI and Hasura)
JWT_SECRET=your_jwt_secret_min_32_chars
```

**Security Note:** Change `POSTGREST_AUTHENTICATOR_PASSWORD` and `JWT_SECRET` in production!

### Step 2: Apply Database Migrations

Run the migration script to create schemas, tables, and functions:

```bash
cd migrations/postgrest
./apply_migrations.sh
```

This will:
1. Install PostgreSQL extensions (`pgcrypto`)
2. Create `auth` schema with users table
3. Create JWT signing/verification functions
4. Create `api` schema with glucose views
5. Implement API functions (`login`, `glucose_statistics`, `user_info`)
6. Create PostgreSQL roles and RLS policies

**Verify migrations:**

```bash
psql -h localhost -p 10000 -U lake -d lakehouse -c "
SELECT schemaname, viewname
FROM pg_views
WHERE schemaname = 'api';
"
```

Expected output:
```
 schemaname |        viewname
------------+--------------------------
 api        | glucose_readings
 api        | glucose_daily_summary
 api        | glucose_hourly_patterns
```

### Step 3: Start PostgREST Service

Start PostgREST using Docker Compose:

```bash
# Start with api profile (includes PostgREST, FastAPI, Hasura)
docker-compose --profile api up -d postgrest

# Or start all services
docker-compose --profile all up -d
```

**Check service status:**

```bash
docker-compose ps postgrest
```

Expected output:
```
NAME        IMAGE                       STATUS
postgrest   postgrest/postgrest:v12.2.3 Up (healthy)
```

**View logs:**

```bash
docker-compose logs -f postgrest
```

Expected logs:
```
postgrest | Listening on port 3000
postgrest | Admin server listening on port 3001
postgrest | Attempting to connect to the database...
postgrest | Connection successful
```

### Step 4: Verify Health Check

Test the admin health endpoint:

```bash
curl http://localhost:10019/live
```

Expected response:
```json
{"status":"UP"}
```

---

## Testing the API

### Test 1: Login and Get JWT Token

```bash
curl -X POST http://localhost:10018/rpc/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst",
    "password": "analyst123"
  }' | jq .
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "uuid-here",
    "username": "analyst",
    "email": "analyst@phlo.local",
    "role": "analyst"
  }
}
```

**Save the token for subsequent requests:**

```bash
TOKEN=$(curl -s -X POST http://localhost:10018/rpc/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "analyst123"}' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Test 2: Get Glucose Readings

```bash
curl "http://localhost:10018/glucose_readings?order=reading_date.desc&limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Expected response (array of glucose readings):
```json
[
  {
    "reading_date": "2024-01-15",
    "day_name": "Monday",
    "avg_glucose_mg_dl": 125.5,
    "reading_count": 288,
    "time_in_range_pct": 78.2
  },
  ...
]
```

### Test 3: Filter Glucose Readings

PostgREST supports powerful filtering via URL parameters:

```bash
# Get readings from a specific date range
curl "http://localhost:10018/glucose_readings?reading_date=gte.2024-01-01&reading_date=lte.2024-01-31" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Get readings where time in range > 70%
curl "http://localhost:10018/glucose_readings?time_in_range_pct=gt.70&order=time_in_range_pct.desc" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Get only specific columns
curl "http://localhost:10018/glucose_readings?select=reading_date,avg_glucose_mg_dl,time_in_range_pct&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Filtering Operators:**
- `eq` - equals
- `gt` - greater than
- `gte` - greater than or equal
- `lt` - less than
- `lte` - less than or equal
- `neq` - not equals
- `like` - LIKE operator (use `*` for wildcard)
- `ilike` - case-insensitive LIKE

### Test 4: Get Daily Summary

```bash
curl "http://localhost:10018/glucose_daily_summary?order=reading_date.desc&limit=7" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Test 5: Get Hourly Patterns

```bash
curl "http://localhost:10018/glucose_hourly_patterns?day_name=eq.Monday" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Test 6: Get Statistics (Function Call)

```bash
# Default 30-day statistics
curl "http://localhost:10018/rpc/glucose_statistics" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Custom period (7 days)
curl "http://localhost:10018/rpc/glucose_statistics?period_days=7" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Expected response:
```json
{
  "period_days": 7,
  "start_date": "2024-01-08",
  "end_date": "2024-01-15",
  "avg_glucose_mg_dl": 128.5,
  "min_glucose_mg_dl": 65,
  "max_glucose_mg_dl": 210,
  "avg_time_in_range_pct": 75.3,
  "total_readings": 2016,
  "days_with_data": 7
}
```

### Test 7: Get Current User Info

```bash
curl "http://localhost:10018/rpc/user_info" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Expected response:
```json
{
  "user_id": "uuid-here",
  "username": "analyst",
  "email": "analyst@phlo.local",
  "role": "analyst"
}
```

### Test 8: Test Authentication Errors

```bash
# Missing token (should return 401)
curl -i "http://localhost:10018/glucose_readings"

# Invalid token (should return 401)
curl -i "http://localhost:10018/glucose_readings" \
  -H "Authorization: Bearer invalid.token.here"
```

### Test 9: Get OpenAPI Documentation

```bash
# Get OpenAPI spec as JSON
curl "http://localhost:10018/" \
  -H "Accept: application/openapi+json" | jq . > openapi.json

# View in browser (Swagger UI)
# Open: http://localhost:10018/
```

---

## Comparing with FastAPI

### Response Format Comparison

**FastAPI** (current):
```bash
curl "http://localhost:10010/api/v1/glucose/readings?limit=1" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**PostgREST** (new):
```bash
curl "http://localhost:10018/glucose_readings?limit=1" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

Both should return similar data structures. If there are differences, adjust the PostgreSQL views in `migrations/postgrest/004_api_schema.sql`.

---

## Monitoring

### Health Checks

**Liveness probe** (is service running?):
```bash
curl http://localhost:10019/live
```

**Readiness probe** (is service ready to accept requests?):
```bash
curl http://localhost:10019/ready
```

### Performance Metrics

PostgREST doesn't include built-in Prometheus metrics, but you can monitor via:

1. **PostgreSQL metrics** (via `postgres-exporter`):
   - Query performance: `pg_stat_statements`
   - Connection pool usage: `pg_stat_activity`

2. **Database logs**:
   ```bash
   docker-compose logs -f postgres | grep "duration:"
   ```

3. **PostgREST logs**:
   ```bash
   docker-compose logs -f postgrest
   ```

---

## Troubleshooting

### Issue: "Connection refused" error

**Symptom:**
```
psql: error: connection to server at "localhost" (127.0.0.1), port 10000 failed: Connection refused
```

**Solution:**
1. Ensure PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Start PostgreSQL if needed:
   ```bash
   docker-compose up -d postgres
   ```

3. Check logs:
   ```bash
   docker-compose logs postgres
   ```

### Issue: "relation does not exist" error

**Symptom:**
```
ERROR:  relation "api.glucose_readings" does not exist
```

**Solution:**
Migrations not applied. Run:
```bash
cd migrations/postgrest
./apply_migrations.sh
```

### Issue: "JWT token invalid or expired"

**Symptom:**
```
HTTP 401 Unauthorized
```

**Solutions:**

1. **Check JWT secret matches:**
   ```bash
   echo $JWT_SECRET
   docker-compose exec postgrest env | grep PGRST_JWT_SECRET
   ```

2. **Regenerate token:**
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:10018/rpc/login \
     -H "Content-Type: application/json" \
     -d '{"username": "analyst", "password": "analyst123"}' | jq -r '.access_token')
   ```

3. **Verify token structure:**
   ```bash
   echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .
   ```

### Issue: "permission denied for schema api"

**Symptom:**
```
ERROR: permission denied for schema api
```

**Solution:**
Role permissions not granted. Re-run migration:
```bash
psql -h localhost -p 10000 -U lake -d lakehouse -f migrations/postgrest/006_roles_and_rls.sql
```

### Issue: PostgREST container keeps restarting

**Check logs:**
```bash
docker-compose logs postgrest
```

**Common causes:**
1. **Database connection failed:** Verify `PGRST_DB_URI` in docker-compose.yml
2. **Invalid configuration:** Check environment variables
3. **Port conflict:** Ensure ports 10018/10019 are not in use

**Verify database connection manually:**
```bash
psql "postgresql://authenticator:authenticator_password_change_in_production@localhost:10000/lakehouse" -c "SELECT 1;"
```

---

## Next Steps

### Phase 2: Nginx Reverse Proxy (Optional)

To maintain backward compatibility with existing FastAPI clients, configure nginx to route requests:

```nginx
# /api/v1/glucose/readings → /glucose_readings
location /api/v1/glucose/readings {
  rewrite ^/api/v1/glucose/readings$ /glucose_readings break;
  proxy_pass http://postgrest:3000;
  proxy_set_header Authorization $http_authorization;
}
```

See PRD section 7.3 for full nginx configuration.

### Phase 3: Testing

Run integration tests:

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/integration/test_postgrest.py -v
```

### Phase 4: Migration

Once validated:
1. Update client applications to use PostgREST endpoints
2. Monitor error rates and performance
3. Gradually shift traffic from FastAPI to PostgREST
4. Decommission FastAPI service

---

## API Reference

### Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/rpc/login` | POST | Authenticate and get JWT token | No |
| `/glucose_readings` | GET | Get glucose readings | Yes |
| `/glucose_daily_summary` | GET | Get daily summary | Yes |
| `/glucose_hourly_patterns` | GET | Get hourly patterns | Yes |
| `/rpc/glucose_statistics` | GET/POST | Get statistics for period | Yes |
| `/rpc/user_info` | GET/POST | Get current user info | Yes |
| `/rpc/health` | GET/POST | Health check | No |
| `/` | GET | OpenAPI spec (with Accept header) | No |

### URL Parameters (for GET requests)

**Filtering:**
```
?column=operator.value
```

Examples:
- `?reading_date=gte.2024-01-01`
- `?avg_glucose_mg_dl=gt.120&time_in_range_pct=gte.70`

**Ordering:**
```
?order=column.asc|desc
```

Examples:
- `?order=reading_date.desc`
- `?order=time_in_range_pct.desc,reading_date.asc`

**Limiting:**
```
?limit=N&offset=M
```

Examples:
- `?limit=10` (first 10 rows)
- `?limit=10&offset=20` (rows 21-30)

**Column selection:**
```
?select=col1,col2,col3
```

Examples:
- `?select=reading_date,avg_glucose_mg_dl`

---

## Resources

- **PostgREST Documentation**: https://postgrest.org
- **PostgREST API Reference**: https://postgrest.org/en/stable/api.html
- **PostgreSQL RLS Guide**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **Migration PRD**: [docs/prd-postgrest-migration.md](prd-postgrest-migration.md)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs postgrest`
2. Verify database connection: `psql -h localhost -p 10000 -U lake -d lakehouse`
3. Review PRD risk mitigation strategies
4. Open GitHub issue with logs and reproduction steps

---

**Last Updated:** 2025-11-21
**Version:** 1.0
**Status:** Ready for Testing
