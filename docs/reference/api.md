# Phlo API Guide

Complete guide to accessing Phlo lakehouse data via REST and GraphQL APIs.

## Overview

Phlo provides two complementary APIs for data access:

1. **FastAPI REST** - Custom endpoints for controlled access to Iceberg and marts
2. **Hasura GraphQL** - Auto-generated GraphQL API from Postgres marts schema

Both APIs share JWT authentication and provide different access patterns for different use cases.

## Quick Start

```bash
# Start prerequisites
make up-query  # Trino + Nessie

# Start API services
make up-api    # FastAPI + Hasura

# Check health
make health-api

# Open interfaces
make api       # FastAPI Swagger docs (http://localhost:8000/docs)
make hasura    # Hasura console (http://localhost:8081/console)
```

## Authentication

### Getting a Token

Both APIs use shared JWT tokens. Login via FastAPI:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "admin_001",
    "username": "admin",
    "email": "admin@phlo.local",
    "role": "admin"
  }
}
```

### Default Users

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | admin | Full access including SQL execution |
| analyst | analyst123 | analyst | Read-only access to all endpoints |

**Production:** Change default passwords in JWT creation code or implement proper user management.

### Using Tokens

**FastAPI:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/glucose/readings
```

**Hasura:**
```bash
curl -X POST http://localhost:8081/v1/graphql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ mrt_glucose_overview { date avg_glucose } }"}'
```

**JavaScript:**
```javascript
const token = "YOUR_TOKEN";

// FastAPI
const response = await fetch('http://localhost:8000/api/v1/glucose/readings', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Hasura
const graphqlResponse = await fetch('http://localhost:8081/v1/graphql', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '{ mrt_glucose_overview { date avg_glucose } }'
  })
});
```

---

## FastAPI REST Endpoints

Base URL: `http://localhost:8000/api/v1`

### Authentication

#### POST `/auth/login`

Get JWT access token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {...}
}
```

---

### Glucose Analytics

Query curated glucose data from Postgres marts (fast, cached).

#### GET `/glucose/readings`

Get glucose readings with optional date filters.

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (default: 1000, max: 10000): Number of readings

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/glucose/readings?start_date=2024-01-01&limit=100"
```

**Response:**
```json
{
  "data": [
    {
      "date": "2024-01-15",
      "avg_glucose": 125.5,
      "min_glucose": 80,
      "max_glucose": 180,
      "readings_count": 288
    }
  ],
  "count": 1,
  "source": "postgres_marts",
  "cached": true
}
```

**Cache:** 1 hour TTL

---

#### GET `/glucose/daily-summary`

Get summary for a specific day.

**Parameters:**
- `date` (required): Date (YYYY-MM-DD)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/glucose/daily-summary?date=2024-01-15"
```

**Response:**
```json
{
  "date": "2024-01-15",
  "avg_glucose": 125.5,
  "min_glucose": 80,
  "max_glucose": 180,
  "readings_count": 288,
  "time_in_range_percent": 85.4
}
```

**Cache:** 1 hour TTL

---

#### GET `/glucose/hourly-patterns`

Get aggregated hourly patterns across all data.

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/glucose/hourly-patterns
```

**Response:**
```json
[
  {
    "hour_of_day": 0,
    "avg_glucose": 110.5,
    "readings_count": 1250
  },
  {
    "hour_of_day": 1,
    "avg_glucose": 108.2,
    "readings_count": 1230
  }
]
```

**Cache:** 6 hours TTL (slow-changing aggregate)

---

#### GET `/glucose/statistics`

Get statistics for a time period.

**Parameters:**
- `period` (default: 7d): Time period (7d, 30d, or 90d)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/glucose/statistics?period=30d"
```

**Response:**
```json
{
  "period": "30d",
  "days": 30,
  "readings_count": 30,
  "statistics": {
    "avg_glucose": 125.5,
    "min_glucose": 80,
    "max_glucose": 200
  }
}
```

**Cache:** 1 hour TTL

---

### Iceberg Data Access

Query raw/bronze/silver/gold Iceberg tables via Trino.

#### GET `/iceberg/tables`

List all Iceberg tables, optionally filtered by schema.

**Parameters:**
- `schema` (optional): Filter by schema (raw, bronze, silver, gold)

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/iceberg/tables?schema=bronze
```

**Response:**
```json
[
  {
    "schema_name": "bronze",
    "table_name": "stg_entries",
    "location": null
  }
]
```

**Cache:** 30 minutes TTL

---

#### GET `/iceberg/{schema}/{table}`

Query data from an Iceberg table.

**Parameters:**
- `filter` (optional): SQL WHERE clause (without 'WHERE')
- `order_by` (optional): SQL ORDER BY clause (without 'ORDER BY')
- `limit` (default: 1000, max: 10000): Number of rows

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/iceberg/bronze/stg_entries?filter=date>='2024-01-01'&limit=10"
```

**Response:**
```json
{
  "schema": "bronze",
  "table": "stg_entries",
  "columns": ["id", "timestamp", "glucose_mg_dl", "date"],
  "rows": [
    ["abc123", "2024-01-01T00:05:00", 120, "2024-01-01"],
    ["def456", "2024-01-01T00:10:00", 125, "2024-01-01"]
  ],
  "row_count": 2,
  "execution_time_ms": 245.3,
  "cached": true
}
```

**Security:**
- SQL injection protection (dangerous keywords rejected)
- 30-second query timeout
- 10,000 row limit enforced

**Cache:** 30 minutes TTL

---

### Advanced Queries (Admin Only)

#### POST `/query/sql`

Execute arbitrary SQL against Trino or Postgres.

**Requires:** Admin role

**Request:**
```json
{
  "query": "SELECT date, avg_glucose FROM iceberg.gold.mrt_glucose_readings LIMIT 10",
  "engine": "trino",
  "limit": 1000
}
```

**Response:**
```json
{
  "columns": ["date", "avg_glucose"],
  "rows": [
    ["2024-01-01", 125.5],
    ["2024-01-02", 130.2]
  ],
  "row_count": 2,
  "execution_time_ms": 156.7
}
```

**Security:**
- Admin-only access
- Write operations blocked (DROP, DELETE, INSERT, UPDATE, CREATE, ALTER)
- Query timeout: 30 seconds
- Row limit: 10,000 max

**No cache** - always executes fresh

---

### Metadata

#### GET `/metadata/health`

API health check (no auth required).

**Example:**
```bash
curl http://localhost:8000/api/v1/metadata/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "phlo-api"
}
```

---

#### GET `/metadata/cache/stats`

Get in-memory cache statistics.

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/metadata/cache/stats
```

**Response:**
```json
{
  "total_entries": 45,
  "active_entries": 42,
  "expired_entries": 3
}
```

---

#### GET `/metadata/user/me`

Get current user information.

**Example:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/metadata/user/me
```

**Response:**
```json
{
  "user_id": "admin_001",
  "username": "admin",
  "email": "admin@phlo.local",
  "role": "admin"
}
```

---

## Hasura GraphQL

Base URL: `http://localhost:8081/v1/graphql`
Console: `http://localhost:8081/console`

### Auto-Generated Schema

Hasura automatically generates GraphQL types from the `marts` schema in Postgres.

**Available Tables:**
- `mrt_glucose_overview` - Daily glucose summaries
- `mrt_glucose_hourly_patterns` - Hourly patterns

### Basic Queries

#### Get Glucose Readings

```graphql
query GetGlucoseReadings($startDate: date!) {
  mrt_glucose_overview(
    where: { date: { _gte: $startDate } }
    order_by: { date: desc }
    limit: 100
  ) {
    date
    avg_glucose
    min_glucose
    max_glucose
    readings_count
    time_in_range_percent
  }
}
```

**Variables:**
```json
{
  "startDate": "2024-01-01"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8081/v1/graphql \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetGlucoseReadings($startDate: date!) { mrt_glucose_overview(where: {date: {_gte: $startDate}}, order_by: {date: desc}, limit: 100) { date avg_glucose min_glucose max_glucose readings_count } }",
    "variables": {"startDate": "2024-01-01"}
  }'
```

---

### Aggregations

```graphql
query GetGlucoseStats {
  mrt_glucose_overview_aggregate(
    where: { date: { _gte: "2024-01-01" } }
  ) {
    aggregate {
      count
      avg {
        avg_glucose
      }
      max {
        max_glucose
      }
      min {
        min_glucose
      }
    }
  }
}
```

---

### Filtering

Hasura supports rich filtering:

```graphql
query GetHighGlucoseDays {
  mrt_glucose_overview(
    where: {
      avg_glucose: { _gt: 140 }
      date: { _gte: "2024-01-01" }
    }
    order_by: { avg_glucose: desc }
  ) {
    date
    avg_glucose
  }
}
```

**Filter Operators:**
- `_eq` - Equal
- `_neq` - Not equal
- `_gt` - Greater than
- `_gte` - Greater than or equal
- `_lt` - Less than
- `_lte` - Less than or equal
- `_in` - In array
- `_is_null` - Is null

---

### Subscriptions (Real-time)

Hasura supports GraphQL subscriptions for real-time data:

```graphql
subscription WatchGlucoseReadings {
  mrt_glucose_overview(
    order_by: { date: desc }
    limit: 10
  ) {
    date
    avg_glucose
  }
}
```

**WebSocket connection required** - see Hasura docs for client setup.

---

## Rate Limiting

API rate limits are role-based:

| Role | Limit |
|------|-------|
| Admin | 1000 requests/minute |
| Analyst | 100 requests/minute |
| Unauthenticated | 50 requests/minute |

**429 Too Many Requests** response when limit exceeded.

---

## Error Handling

### FastAPI Error Responses

```json
{
  "detail": "Error message",
  "error": "Exception details",
  "path": "/api/v1/glucose/readings"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `429` - Too many requests
- `500` - Internal server error

### Hasura Error Responses

```json
{
  "errors": [
    {
      "message": "Error description",
      "extensions": {
        "path": "$.query",
        "code": "validation-failed"
      }
    }
  ]
}
```

---

## Performance & Caching

### Cache Strategy

| Endpoint | TTL | Reasoning |
|----------|-----|-----------|
| `/glucose/readings` | 1 hour | Fast-changing data |
| `/glucose/hourly-patterns` | 6 hours | Slow-changing aggregates |
| `/iceberg/*` | 30 minutes | Balance freshness/performance |
| `/query/sql` | None | Always fresh |

### Cache Headers

Responses include cache metadata in JSON body:
```json
{
  "cached": true,
  "source": "postgres_marts"
}
```

### Query Optimization

**Fast queries (use these for dashboards):**
- `/glucose/*` endpoints → Postgres marts (pre-aggregated)
- Hasura queries → Postgres marts (indexed)

**Slower queries (use for exploration):**
- `/iceberg/*` endpoints → Trino (full table scans possible)
- `/query/sql` with Trino → Analytical queries

---

## Security Best Practices

### Production Checklist

- [ ] **Change JWT secret** - Update `JWT_SECRET` in `.env`
- [ ] **Change Hasura admin secret** - Update `HASURA_ADMIN_SECRET`
- [ ] **Change default passwords** - Update hardcoded users in `app/auth/jwt.py`
- [ ] **Enable HTTPS** - Use reverse proxy (nginx/Caddy)
- [ ] **Restrict CORS** - Update `HASURA_GRAPHQL_CORS_DOMAIN`
- [ ] **Add API gateway** - Kong/Traefik for additional security
- [ ] **Monitor rate limits** - Check Prometheus metrics
- [ ] **Audit logs** - Enable request logging
- [ ] **Network isolation** - Internal network for API → database

### JWT Token Security

**Token expiration:** 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)

**Refresh tokens:** Not implemented (add if needed for long-lived sessions)

**Token revocation:** Not implemented (add Redis blacklist if needed)

---

## Integration Examples

### Python

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'analyst',
    'password': 'analyst123'
})
token = response.json()['access_token']

# Get readings
headers = {'Authorization': f'Bearer {token}'}
readings = requests.get(
    'http://localhost:8000/api/v1/glucose/readings',
    headers=headers,
    params={'start_date': '2024-01-01', 'limit': 100}
).json()

print(f"Retrieved {readings['count']} readings")
```

### JavaScript/TypeScript

```typescript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'analyst', password: 'analyst123' })
});
const { access_token } = await loginResponse.json();

// Get readings
const readingsResponse = await fetch(
  'http://localhost:8000/api/v1/glucose/readings?start_date=2024-01-01',
  { headers: { 'Authorization': `Bearer ${access_token}` } }
);
const readings = await readingsResponse.json();
console.log(`Retrieved ${readings.count} readings`);
```

### GraphQL with Apollo Client

```typescript
import { ApolloClient, InMemoryCache, createHttpLink, gql } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: 'http://localhost:8081/v1/graphql',
});

const authLink = setContext((_, { headers }) => {
  const token = 'YOUR_TOKEN';
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  }
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache()
});

// Query
const { data } = await client.query({
  query: gql`
    query GetGlucoseReadings {
      mrt_glucose_overview(order_by: {date: desc}, limit: 10) {
        date
        avg_glucose
      }
    }
  `
});
```

---

## Extending the API

### Adding New Endpoints

1. **Create router** in `services/api/app/routers/my_endpoint.py`
2. **Add connector** if new data source in `services/api/app/connectors/`
3. **Define schemas** in `services/api/app/models/schemas.py`
4. **Register router** in `services/api/app/main.py`

**Example:**
```python
# services/api/app/routers/weather.py
from fastapi import APIRouter
from app.auth.dependencies import CurrentUser

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/forecast")
async def get_forecast(current_user: CurrentUser):
    return {"forecast": "sunny"}

# services/api/app/main.py
from app.routers import weather
app.include_router(weather.router, prefix=settings.api_prefix)
```

### Adding Hasura Tables

Hasura automatically tracks new tables in the `marts` schema:

1. Create table in Postgres `marts` schema (via dbt or SQL)
2. Open Hasura console: `make hasura`
3. Navigate to **Data** → **Track Tables**
4. Click **Track** on your new table
5. Set permissions for `admin` and `analyst` roles

---

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker compose logs api
docker compose logs hasura

# Verify dependencies running
make health  # Check Postgres and Trino

# Rebuild
docker compose build api
docker compose up -d api
```

### Authentication Failures

```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Check JWT secret matches between API and Hasura
docker compose exec api env | grep JWT_SECRET
```

### Slow Queries

```bash
# Check cache stats
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/metadata/cache/stats

# Check Trino query performance
make trino  # Open Trino UI, check query history
```

### Hasura Permissions Issues

1. Open Hasura console: `make hasura`
2. Navigate to **Data** → Select table → **Permissions**
3. Ensure `admin` and `analyst` roles have `select` permission
4. Check row-level permissions (leave empty for full access)

---

## Monitoring

### Prometheus Metrics

FastAPI exports metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Key metrics:**
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests

Add to Prometheus scrape config if observability stack running.

### Logs

```bash
# FastAPI logs
docker compose logs -f api

# Hasura logs
docker compose logs -f hasura

# All API logs in Grafana (if observability running)
# LogQL: {cascade_component=~"phlo-api|hasura"}
```

---

## Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | 8000 | FastAPI port |
| `JWT_SECRET` | (default) | **Change in production** |
| `JWT_ALGORITHM` | HS256 | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Token expiration |
| `HASURA_PORT` | 8081 | Hasura port |
| `HASURA_VERSION` | v2.45.0 | Hasura version |
| `HASURA_ADMIN_SECRET` | (default) | **Change in production** |

### API Versions

- FastAPI: Latest
- Hasura: v2.45.0
- OpenAPI Spec: 3.1.0

### Useful Links

- FastAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
- Hasura Console: http://localhost:8081/console
- Hasura GraphiQL: http://localhost:8081/console/api/api-explorer
