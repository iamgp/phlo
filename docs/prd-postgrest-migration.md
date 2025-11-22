# Product Requirements Document: FastAPI to PostgREST Migration

**Version**: 1.0
**Date**: 2025-11-21
**Author**: Claude (AI Assistant)
**Status**: Draft
**Project**: Phlo Lakehouse API Modernization

---

## Executive Summary

This PRD outlines the migration of the Phlo Lakehouse REST API from a custom FastAPI implementation to PostgREST, a declarative REST API layer that automatically generates RESTful endpoints from PostgreSQL database schemas. This migration aims to reduce code complexity, improve maintainability, and leverage PostgreSQL's native capabilities for authentication, authorization, and data access.

**Key Benefits:**
- **Reduced Code Complexity**: Eliminate ~2,000+ lines of custom API code
- **Lower Maintenance Burden**: Remove custom routing, serialization, and query logic
- **Enhanced Performance**: Leverage PostgreSQL query optimization and connection pooling
- **Declarative Security**: Database-native Row-Level Security (RLS) policies
- **Auto-Generated OpenAPI**: Automatic API documentation from database schema

---

## Background and Context

### Current State

The Phlo Lakehouse platform currently uses a **FastAPI-based REST API** (`/services/api/app/`) with:

- **15+ custom endpoints** across 5 route modules (auth, glucose, iceberg, query, metadata)
- **Dual database architecture**: PostgreSQL for marts, Trino for Iceberg queries
- **Custom JWT authentication** with role-based access control (admin, analyst)
- **Manual Pydantic schemas** for request/response validation
- **In-memory caching middleware** with configurable TTLs
- **Custom rate limiting** based on user roles
- **Hand-written SQL queries** in Python code

**Technology Stack:**
- FastAPI (Python 3.11+)
- psycopg2 for PostgreSQL connectivity
- python-jose for JWT handling
- Custom middleware for caching and rate limiting

### Problem Statement

The current FastAPI implementation has several challenges:

1. **High Maintenance Overhead**: Every database schema change requires updating Pydantic models, route handlers, and SQL queries
2. **Code Duplication**: Similar CRUD patterns repeated across multiple endpoints
3. **Testing Complexity**: Requires mocking database connections and authentication layers
4. **Performance Bottlenecks**: Python-based serialization and connection management
5. **Limited Filtering**: Custom query parameter parsing for each endpoint
6. **Inconsistent Error Handling**: Varies across different route modules
7. **Trino Dependency**: Complex dual-database routing logic

### Why PostgREST?

**PostgREST** is a standalone web server that automatically generates a RESTful API from a PostgreSQL database schema. It provides:

- **Zero-Code API Generation**: Endpoints auto-created from tables, views, and functions
- **Advanced Filtering**: Full support for filtering, ordering, pagination, and aggregation via URL parameters
- **Database-Native Auth**: JWT authentication with PostgreSQL RLS policies
- **OpenAPI Auto-Generation**: Always up-to-date API documentation
- **High Performance**: Written in Haskell, optimized for PostgreSQL
- **Proven Track Record**: Used in production by thousands of organizations

---

## Goals and Objectives

### Primary Goals

1. **Reduce API Code Complexity** by 80%+ through declarative schema-driven development
2. **Improve API Performance** by leveraging PostgreSQL query optimization and PostgREST's efficient connection pooling
3. **Enhance Developer Experience** by eliminating manual schema synchronization
4. **Maintain Feature Parity** with existing FastAPI endpoints (authentication, glucose analytics, metadata)
5. **Preserve Security Model** with JWT authentication and role-based access control

### Non-Goals (Out of Scope)

- **Trino/Iceberg Migration**: Initial PostgREST implementation will focus on PostgreSQL marts. Trino queries will remain in a separate microservice or be handled via stored procedures
- **UI Changes**: Frontend applications (Superset, custom dashboards) will adapt to new API with minimal changes
- **Real-Time Features**: WebSocket/SSE support is not included in Phase 1
- **Custom Business Logic**: Complex computations will move to PostgreSQL stored procedures rather than application code

### Success Criteria

- ✅ All existing glucose analytics endpoints accessible via PostgREST
- ✅ JWT authentication working with Hasura-compatible tokens
- ✅ Row-level security policies enforcing role-based access
- ✅ API response times within 20% of current FastAPI performance
- ✅ Zero breaking changes for existing API clients
- ✅ Comprehensive OpenAPI documentation auto-generated
- ✅ Test coverage >80% for database functions and RLS policies

---

## User Stories

### As an API Consumer (Data Analyst)

- **US-1**: As a data analyst, I want to query glucose readings with flexible filters (date ranges, glucose thresholds) so I can analyze specific time periods
- **US-2**: As a data analyst, I want to retrieve daily glucose summaries with statistical aggregations so I can identify trends
- **US-3**: As a data analyst, I want to access hourly glucose patterns so I can understand time-of-day effects
- **US-4**: As a data analyst, I want to authenticate with a JWT token so my API requests are secure
- **US-5**: As a data analyst, I want to see clear error messages when queries fail so I can debug issues

### As an Administrator

- **US-6**: As an admin, I want to execute custom SQL queries against the database so I can perform ad-hoc analysis
- **US-7**: As an admin, I want to manage user roles and permissions via database policies so I can control access
- **US-8**: As an admin, I want to view API health metrics so I can monitor system performance

### As a Developer

- **US-9**: As a developer, I want database schema changes to automatically reflect in the API so I don't manually update code
- **US-10**: As a developer, I want comprehensive API documentation that's always up-to-date so I can integrate quickly
- **US-11**: As a developer, I want to write unit tests for database functions so I can ensure correctness

### As a Platform Engineer

- **US-12**: As a platform engineer, I want to deploy the API as a stateless service so I can scale horizontally
- **US-13**: As a platform engineer, I want to monitor API performance via Prometheus metrics so I can track SLAs
- **US-14**: As a platform engineer, I want to configure the API via environment variables so I can manage deployments

---

## Technical Requirements

### Functional Requirements

#### FR-1: Core Data Access

| Endpoint | Method | Description | PostgREST Implementation |
|----------|--------|-------------|--------------------------|
| `/glucose_readings` | GET | Fetch glucose readings with filters | Direct table/view access with URL parameters |
| `/glucose_daily_summary` | GET | Daily aggregated glucose metrics | Materialized view or function |
| `/glucose_hourly_patterns` | GET | Hourly patterns across all data | Materialized view or function |
| `/glucose_statistics` | GET | Rolling 7d/30d/90d statistics | PostgreSQL function returning JSON |
| `/iceberg_tables` | GET | List Iceberg tables (future) | Foreign data wrapper or external service |
| `/user_me` | GET | Current authenticated user info | PostgreSQL function reading JWT claims |

**Implementation Approach:**
- Expose existing `marts.mrt_glucose_overview` and `marts.mrt_glucose_hourly_patterns` as API views
- Create PostgreSQL functions for computed endpoints (statistics, user info)
- Use PostgREST's filtering DSL for advanced queries

#### FR-2: Authentication & Authorization

| Requirement | Current FastAPI | PostgREST Implementation |
|-------------|-----------------|--------------------------|
| Authentication Method | JWT (HS256) | JWT (HS256) via `pgrst-jwt-secret` |
| Token Validation | Python `python-jose` library | PostgREST built-in JWT verification |
| User Storage | In-memory dictionary | `auth.users` PostgreSQL table |
| Password Hashing | bcrypt (passlib) | pgcrypto extension |
| Token Endpoint | `/api/v1/auth/login` (FastAPI) | `/rpc/login` (PostgreSQL function) |
| User Roles | JWT claim `role` | PostgreSQL roles (`analyst`, `admin`) |
| Authorization | Dependency injection | Row-Level Security (RLS) policies |

**JWT Token Structure:**
```json
{
  "user_id": "uuid",
  "username": "string",
  "email": "string",
  "role": "admin|analyst",
  "exp": 1234567890,
  "https://hasura.io/jwt/claims": {
    "x-hasura-allowed-roles": ["admin", "analyst"],
    "x-hasura-default-role": "analyst",
    "x-hasura-user-id": "uuid"
  }
}
```

**RLS Policy Example:**
```sql
-- Only admins can execute custom SQL via stored procedures
CREATE POLICY admin_only_queries ON query_results
  FOR ALL
  TO authenticated
  USING (current_setting('request.jwt.claims', true)::json->>'role' = 'admin');
```

#### FR-3: Advanced Features

| Feature | Current Implementation | PostgREST Implementation |
|---------|------------------------|--------------------------|
| Caching | In-memory Python dict with TTLs | PostgreSQL materialized views + `Cache-Control` headers |
| Rate Limiting | Custom middleware (role-based) | PostgreSQL extension (pg_cron + custom schema) or nginx |
| Query Limits | Python code (max 10,000 rows) | PostgREST `max-rows` configuration |
| SQL Injection Protection | Keyword blacklist in Python | PostgreSQL prepared statements (built-in) |
| Query Timeout | Python asyncio timeout (30s) | PostgreSQL `statement_timeout` |
| Health Checks | `/health` endpoint | `/` root endpoint (PostgREST introspection) |
| Metrics | Custom Prometheus metrics | PostgREST built-in metrics or pg_stat_statements |

#### FR-4: API Compatibility

To ensure zero breaking changes for existing clients:

1. **URL Path Mapping**: Use nginx reverse proxy to rewrite URLs
   ```nginx
   # Map old FastAPI paths to PostgREST
   location /api/v1/glucose/readings {
     rewrite ^/api/v1/glucose/readings$ /glucose_readings break;
     proxy_pass http://postgrest:3000;
   }
   ```

2. **Response Format**: Ensure PostgREST JSON responses match FastAPI structure
   - Use PostgreSQL views to reshape data
   - Custom PostgreSQL functions for complex transformations

3. **Error Handling**: Map PostgREST HTTP error codes to match FastAPI conventions

### Non-Functional Requirements

#### NFR-1: Performance

- **Response Time**: P95 latency < 200ms for simple queries (< 500ms for aggregations)
- **Throughput**: Support 100 concurrent requests per second
- **Connection Pooling**: Maintain connection pool of 20-50 connections via PgBouncer
- **Caching**: Implement HTTP caching with appropriate `Cache-Control` headers

#### NFR-2: Security

- **Encryption**: All API traffic over HTTPS (TLS 1.2+)
- **Authentication**: JWT tokens with 60-minute expiration
- **Authorization**: Row-Level Security policies for all tables/views
- **SQL Injection**: Zero risk via PostgREST's prepared statements
- **Secrets Management**: JWT secret via environment variables (never hardcoded)

#### NFR-3: Scalability

- **Horizontal Scaling**: Run multiple PostgREST instances behind load balancer
- **Database Scaling**: PostgreSQL read replicas for query distribution
- **Resource Limits**: CPU/memory limits via Docker or Kubernetes

#### NFR-4: Observability

- **Logging**: Structured JSON logs with request IDs
- **Metrics**: Expose Prometheus metrics (request count, latency, error rate)
- **Tracing**: OpenTelemetry-compatible traces (future enhancement)
- **Health Checks**: `/` endpoint returns 200 OK when healthy

#### NFR-5: Maintainability

- **Documentation**: Auto-generated OpenAPI 3.0 spec at `/`
- **Testing**: pgTAP tests for database functions and RLS policies
- **Version Control**: Database migrations via Alembic or Flyway
- **Rollback**: Blue-green deployment for zero-downtime rollbacks

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  Superset Dashboards | API Clients | Hasura GraphQL        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  REVERSE PROXY (nginx)                      │
│  • Path rewriting (/api/v1/* → /*)                         │
│  • Rate limiting (optional)                                 │
│  • TLS termination                                          │
│  • Load balancing                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │    PostgREST     │◄─JWT─►│  Hasura GraphQL  │          │
│  │   (Port 3000)    │        │  (Port 10011)    │          │
│  │                  │        │                  │          │
│  │ • Auto REST API  │        │ • Auto GraphQL   │          │
│  │ • JWT auth       │        │ • Subscriptions  │          │
│  │ • OpenAPI docs   │        │ • Relationships  │          │
│  └──────────────────┘        └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              CONNECTION POOLER (PgBouncer)                  │
│  • Transaction pooling                                      │
│  • Connection reuse                                         │
│  • Health monitoring                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                       │
│  ┌──────────────────────────────────────────────┐          │
│  │              Database Schemas                │          │
│  │                                              │          │
│  │  auth:     users, sessions                  │          │
│  │  api:      glucose_readings (view)          │          │
│  │            glucose_daily_summary (view)     │          │
│  │            glucose_hourly_patterns (view)   │          │
│  │            glucose_statistics (function)    │          │
│  │            login (function)                 │          │
│  │            user_info (function)             │          │
│  │  marts:    mrt_glucose_overview (table)     │          │
│  │            mrt_glucose_hourly_patterns      │          │
│  │  public:   health_check (function)          │          │
│  │                                              │          │
│  │  Extensions: pgcrypto, pgjwt                │          │
│  │  RLS Policies: analyst_read, admin_all      │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Design

#### Schema Organization

```sql
-- Authentication schema (not exposed via API)
CREATE SCHEMA IF NOT EXISTS auth;

-- API schema (exposed via PostgREST)
CREATE SCHEMA IF NOT EXISTS api;

-- Marts schema (source data)
CREATE SCHEMA IF NOT EXISTS marts;
```

#### Core Tables and Views

**1. Authentication: `auth.users`**
```sql
CREATE TABLE auth.users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,  -- bcrypt hash
  role VARCHAR(20) NOT NULL DEFAULT 'analyst',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

-- Index for login lookups
CREATE INDEX idx_users_username ON auth.users(username) WHERE is_active = TRUE;
```

**2. API Views: Glucose Data**
```sql
-- Expose marts data via API schema
CREATE OR REPLACE VIEW api.glucose_readings AS
SELECT
  reading_date,
  reading_count,
  avg_glucose_mg_dl,
  min_glucose_mg_dl,
  max_glucose_mg_dl,
  time_in_range_pct,
  time_below_range_pct,
  time_above_range_pct
FROM marts.mrt_glucose_overview;

CREATE OR REPLACE VIEW api.glucose_daily_summary AS
SELECT
  reading_date,
  day_name,
  week_of_year,
  month,
  year,
  reading_count,
  avg_glucose_mg_dl,
  time_in_range_pct,
  estimated_a1c_pct
FROM marts.mrt_glucose_overview
ORDER BY reading_date DESC;

CREATE OR REPLACE VIEW api.glucose_hourly_patterns AS
SELECT
  hour_of_day,
  day_of_week,
  day_name,
  reading_count,
  avg_glucose_mg_dl,
  median_glucose_mg_dl,
  time_in_range_pct
FROM marts.mrt_glucose_hourly_patterns
ORDER BY day_of_week, hour_of_day;
```

**3. API Functions: Computed Endpoints**
```sql
-- Login function (replaces /api/v1/auth/login)
CREATE OR REPLACE FUNCTION api.login(username TEXT, password TEXT)
RETURNS JSON AS $$
DECLARE
  user_record RECORD;
  token TEXT;
BEGIN
  -- Validate credentials
  SELECT * INTO user_record
  FROM auth.users
  WHERE auth.users.username = login.username
    AND auth.users.is_active = TRUE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Invalid credentials'
      USING HINT = 'Please check your username and password';
  END IF;

  -- Verify password
  IF NOT (user_record.password_hash = crypt(password, user_record.password_hash)) THEN
    RAISE EXCEPTION 'Invalid credentials'
      USING HINT = 'Please check your username and password';
  END IF;

  -- Generate JWT token (using pgjwt extension)
  token := sign(
    json_build_object(
      'user_id', user_record.user_id,
      'username', user_record.username,
      'email', user_record.email,
      'role', user_record.role,
      'exp', extract(epoch from now() + interval '60 minutes'),
      'https://hasura.io/jwt/claims', json_build_object(
        'x-hasura-allowed-roles', ARRAY[user_record.role],
        'x-hasura-default-role', user_record.role,
        'x-hasura-user-id', user_record.user_id::text
      )
    ),
    current_setting('app.jwt_secret')
  );

  RETURN json_build_object(
    'access_token', token,
    'token_type', 'Bearer',
    'expires_in', 3600,
    'user', json_build_object(
      'user_id', user_record.user_id,
      'username', user_record.username,
      'email', user_record.email,
      'role', user_record.role
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Glucose statistics function (replaces /api/v1/glucose/statistics)
CREATE OR REPLACE FUNCTION api.glucose_statistics(period_days INT DEFAULT 30)
RETURNS JSON AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'period_days', period_days,
    'avg_glucose_mg_dl', ROUND(AVG(avg_glucose_mg_dl), 1),
    'min_glucose_mg_dl', MIN(min_glucose_mg_dl),
    'max_glucose_mg_dl', MAX(max_glucose_mg_dl),
    'avg_time_in_range_pct', ROUND(AVG(time_in_range_pct), 1),
    'avg_estimated_a1c_pct', ROUND(AVG(estimated_a1c_pct), 2),
    'readings_count', SUM(reading_count)
  ) INTO result
  FROM marts.mrt_glucose_overview
  WHERE reading_date >= CURRENT_DATE - (period_days || ' days')::interval;

  RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Current user info (replaces /api/v1/metadata/user/me)
CREATE OR REPLACE FUNCTION api.user_info()
RETURNS JSON AS $$
BEGIN
  RETURN json_build_object(
    'user_id', current_setting('request.jwt.claims', true)::json->>'user_id',
    'username', current_setting('request.jwt.claims', true)::json->>'username',
    'email', current_setting('request.jwt.claims', true)::json->>'email',
    'role', current_setting('request.jwt.claims', true)::json->>'role'
  );
EXCEPTION
  WHEN undefined_object THEN
    RAISE EXCEPTION 'Not authenticated'
      USING HINT = 'Please provide a valid JWT token';
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
```

#### Row-Level Security Policies

```sql
-- Enable RLS on all API views
ALTER VIEW api.glucose_readings ENABLE ROW LEVEL SECURITY;
ALTER VIEW api.glucose_daily_summary ENABLE ROW LEVEL SECURITY;
ALTER VIEW api.glucose_hourly_patterns ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read all glucose data
CREATE POLICY authenticated_read_glucose ON api.glucose_readings
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY authenticated_read_summary ON api.glucose_daily_summary
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY authenticated_read_patterns ON api.glucose_hourly_patterns
  FOR SELECT
  TO authenticated
  USING (true);

-- PostgreSQL roles
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE analyst NOLOGIN IN ROLE authenticated;
CREATE ROLE admin NOLOGIN IN ROLE authenticated;

-- Grant permissions
GRANT USAGE ON SCHEMA api TO anon, authenticated;
GRANT SELECT ON api.glucose_readings TO authenticated;
GRANT SELECT ON api.glucose_daily_summary TO authenticated;
GRANT SELECT ON api.glucose_hourly_patterns TO authenticated;
GRANT EXECUTE ON FUNCTION api.glucose_statistics TO authenticated;
GRANT EXECUTE ON FUNCTION api.user_info TO authenticated;
GRANT EXECUTE ON FUNCTION api.login TO anon;  -- Login doesn't require auth
```

### PostgREST Configuration

**`postgrest.conf`**
```conf
# Database connection
db-uri = "postgres://authenticator:secret@postgres:5432/lakehouse"
db-schemas = "api"
db-anon-role = "anon"

# JWT authentication
jwt-secret = "${JWT_SECRET}"  # Same secret as FastAPI
jwt-secret-is-base64 = false
jwt-aud = "phlo-api"

# API configuration
server-host = "0.0.0.0"
server-port = 3000
openapi-mode = "follow-privileges"
openapi-server-proxy-uri = "http://localhost:10010"

# Security
db-max-rows = 10000
db-pre-request = "api.check_rate_limit"  # Optional rate limiting function
db-tx-end = "commit"
db-use-legacy-gucs = false

# Performance
db-pool = 20
db-pool-timeout = 10
db-extra-search-path = "public"

# Logging
log-level = "info"
```

### Nginx Reverse Proxy Configuration

**`nginx.conf`**
```nginx
upstream postgrest {
  server postgrest:3000;
}

upstream hasura {
  server hasura:8080;
}

server {
  listen 10010;
  server_name localhost;

  # PostgREST (REST API)
  location /api/v1/auth/login {
    rewrite ^/api/v1/auth/login$ /rpc/login break;
    proxy_pass http://postgrest;
    proxy_set_header Content-Type application/json;
  }

  location /api/v1/glucose/readings {
    rewrite ^/api/v1/glucose/readings$ /glucose_readings break;
    proxy_pass http://postgrest;
  }

  location /api/v1/glucose/daily-summary {
    rewrite ^/api/v1/glucose/daily-summary$ /glucose_daily_summary break;
    proxy_pass http://postgrest;
  }

  location /api/v1/glucose/hourly-patterns {
    rewrite ^/api/v1/glucose/hourly-patterns$ /glucose_hourly_patterns break;
    proxy_pass http://postgrest;
  }

  location /api/v1/glucose/statistics {
    rewrite ^/api/v1/glucose/statistics$ /rpc/glucose_statistics break;
    proxy_pass http://postgrest;
  }

  location /api/v1/metadata/user/me {
    rewrite ^/api/v1/metadata/user/me$ /rpc/user_info break;
    proxy_pass http://postgrest;
  }

  location /api/v1/metadata/health {
    rewrite ^/api/v1/metadata/health$ / break;
    proxy_pass http://postgrest;
  }

  # OpenAPI documentation
  location /docs {
    rewrite ^/docs$ / break;
    proxy_pass http://postgrest;
    proxy_set_header Accept application/openapi+json;
  }

  # Hasura GraphQL
  location /v1/graphql {
    proxy_pass http://hasura;
  }
}
```

---

## Migration Strategy

### Phase 1: Database Schema Preparation (Week 1-2)

**Objectives:**
- Create API schema and views
- Implement authentication tables and functions
- Write RLS policies
- Set up database roles

**Tasks:**
1. Create migration scripts for schema changes
2. Write `auth.users` table and seed with existing users
3. Implement `api.login()` function with JWT generation
4. Create API views for glucose data
5. Write RLS policies for all exposed views
6. Install PostgreSQL extensions (pgcrypto, pgjwt)
7. Test database functions with pgTAP

**Deliverables:**
- ✅ Database migration scripts in `/migrations/postgrest/`
- ✅ Seed data for test users
- ✅ pgTAP test suite with >80% coverage
- ✅ Documentation for database schema

### Phase 2: PostgREST Deployment (Week 2-3)

**Objectives:**
- Deploy PostgREST alongside existing FastAPI
- Configure nginx reverse proxy
- Implement observability (logging, metrics)

**Tasks:**
1. Create `postgrest.conf` configuration file
2. Write Docker Compose service for PostgREST
3. Configure nginx reverse proxy with path rewriting
4. Set up PgBouncer connection pooler
5. Implement health checks and readiness probes
6. Configure Prometheus metrics scraping
7. Test all endpoints with Postman/curl

**Deliverables:**
- ✅ PostgREST running on port 3000 (internal)
- ✅ Nginx proxy on port 10010 with path rewriting
- ✅ Grafana dashboard for PostgREST metrics
- ✅ Deployment documentation

### Phase 3: Parallel Operation & Testing (Week 3-4)

**Objectives:**
- Run PostgREST and FastAPI in parallel
- Perform load testing and performance comparison
- Validate feature parity

**Tasks:**
1. Configure dual-proxy setup (FastAPI on `:10010/fastapi`, PostgREST on `:10010/api`)
2. Write integration tests comparing responses
3. Perform load testing with Apache Bench / k6
4. Compare response times and error rates
5. Validate JWT token compatibility with Hasura
6. Test edge cases (missing tokens, invalid filters, etc.)
7. Document any response format differences

**Deliverables:**
- ✅ Integration test suite (Pytest)
- ✅ Load test results (response times, throughput)
- ✅ Comparison report (FastAPI vs PostgREST)
- ✅ Bug fixes for any discovered issues

### Phase 4: Client Migration (Week 4-5)

**Objectives:**
- Update API clients to use PostgREST endpoints
- Validate Superset dashboards still work
- Monitor for errors in production

**Tasks:**
1. Update Superset dashboard queries (if needed)
2. Test external API clients (if any)
3. Monitor error logs for 404s or auth failures
4. Implement gradual rollout (10% → 50% → 100%)
5. Set up alerts for elevated error rates

**Deliverables:**
- ✅ Zero breaking changes for clients
- ✅ Monitoring dashboard showing traffic split
- ✅ Runbook for rollback procedure

### Phase 5: FastAPI Deprecation (Week 5-6)

**Objectives:**
- Redirect all traffic to PostgREST
- Decommission FastAPI service
- Clean up deprecated code

**Tasks:**
1. Update nginx config to remove FastAPI upstream
2. Stop FastAPI service in Docker Compose
3. Archive FastAPI codebase (`/archive/fastapi/`)
4. Update documentation and README files
5. Remove unused Python dependencies
6. Celebrate! 🎉

**Deliverables:**
- ✅ FastAPI service stopped
- ✅ Archived codebase for reference
- ✅ Updated architecture documentation
- ✅ Blog post summarizing migration learnings

### Rollback Plan

If critical issues arise during migration:

1. **Immediate Rollback**: Revert nginx config to route 100% traffic to FastAPI
2. **Database Rollback**: Keep FastAPI database queries unchanged (no schema changes until Phase 5)
3. **Monitoring**: Alert if PostgREST error rate >5% or p95 latency >500ms
4. **Decision Point**: If issues persist >4 hours, rollback and investigate offline

---

## Testing Strategy

### Unit Tests (Database Functions)

Use **pgTAP** for testing PostgreSQL functions and views:

```sql
-- Test login function
BEGIN;
SELECT plan(5);

-- Test successful login
SELECT ok(
  (api.login('analyst', 'analyst123')->>'access_token') IS NOT NULL,
  'Login returns JWT token'
);

-- Test invalid password
SELECT throws_ok(
  'SELECT api.login(''analyst'', ''wrongpassword'')',
  'Invalid credentials'
);

-- Test inactive user
SELECT throws_ok(
  'SELECT api.login(''inactive_user'', ''password'')',
  'Invalid credentials'
);

SELECT finish();
ROLLBACK;
```

### Integration Tests (API Endpoints)

Use **Pytest** with `httpx` for testing PostgREST endpoints:

```python
import httpx
import pytest

BASE_URL = "http://localhost:10010/api/v1"

@pytest.fixture
def auth_token():
    """Get JWT token for testing."""
    response = httpx.post(f"{BASE_URL}/auth/login", json={
        "username": "analyst",
        "password": "analyst123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

def test_glucose_readings(auth_token):
    """Test glucose readings endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = httpx.get(
        f"{BASE_URL}/glucose/readings",
        headers=headers,
        params={"reading_date": "gte.2024-01-01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_unauthorized_access():
    """Test that endpoints require authentication."""
    response = httpx.get(f"{BASE_URL}/glucose/readings")
    assert response.status_code == 401
```

### Load Tests (Performance)

Use **k6** for load testing:

```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp up to 50 users
    { duration: '3m', target: 50 },  // Stay at 50 users
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests <200ms
    http_req_failed: ['rate<0.05'],     // Error rate <5%
  },
};

export default function () {
  const params = {
    headers: {
      'Authorization': `Bearer ${__ENV.JWT_TOKEN}`,
    },
  };

  let res = http.get('http://localhost:10010/api/v1/glucose/readings', params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
}
```

---

## Success Metrics

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p50) | < 50ms | Prometheus `http_request_duration_seconds` |
| API Response Time (p95) | < 200ms | Prometheus `http_request_duration_seconds` |
| API Response Time (p99) | < 500ms | Prometheus `http_request_duration_seconds` |
| Error Rate | < 1% | Prometheus `http_requests_total{status=~"5.."}` |
| Throughput | > 100 req/s | Prometheus `rate(http_requests_total[1m])` |
| Database Connection Pool Utilization | < 80% | PgBouncer metrics |

### Code Complexity Metrics

| Metric | Current (FastAPI) | Target (PostgREST) | Improvement |
|--------|-------------------|---------------------|-------------|
| Lines of Python Code | ~2,000 | ~0 | -100% |
| API Route Files | 5 files | 0 files | -100% |
| Manual SQL Queries | ~15 queries | 0 queries | -100% |
| Pydantic Schemas | ~10 schemas | 0 schemas | -100% |
| Database Functions | 0 | ~5-10 | New capability |
| RLS Policies | 0 | ~5-10 | New capability |

### Developer Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to Add New Endpoint | < 10 minutes | Survey + observation |
| API Documentation Up-to-Date | 100% | Auto-generated by PostgREST |
| Test Coverage (DB Functions) | > 80% | pgTAP coverage report |
| Deployment Time | < 5 minutes | CI/CD pipeline duration |

---

## Risks and Mitigations

### Risk 1: Performance Regression

**Description**: PostgREST may have higher latency than FastAPI for some queries.

**Likelihood**: Medium
**Impact**: High

**Mitigation**:
- Run comprehensive load tests in Phase 3 before migration
- Use PgBouncer for connection pooling
- Implement PostgreSQL query optimization (indexes, materialized views)
- Enable HTTP caching with `Cache-Control` headers
- Monitor performance metrics continuously

**Rollback**: If p95 latency >500ms, rollback to FastAPI

### Risk 2: Feature Gaps

**Description**: PostgREST may not support all custom business logic in FastAPI.

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Move complex logic to PostgreSQL stored procedures
- Keep Trino queries in separate microservice (out of scope for Phase 1)
- Document any unsupported features and defer to Phase 2

**Acceptance Criteria**: All glucose analytics endpoints must have feature parity

### Risk 3: Authentication Compatibility

**Description**: JWT tokens may not be compatible with Hasura or existing clients.

**Likelihood**: Low
**Impact**: High

**Mitigation**:
- Use identical JWT structure and secret as FastAPI
- Test Hasura integration in Phase 2
- Implement token validation tests in integration suite

**Rollback**: If Hasura auth fails, rollback immediately

### Risk 4: Learning Curve

**Description**: Team may lack expertise in PostgREST and PostgreSQL functions.

**Likelihood**: High
**Impact**: Low

**Mitigation**:
- Allocate 1 week for team training on PostgREST and PL/pgSQL
- Create internal documentation and code examples
- Pair programming sessions for writing stored procedures
- Community support via PostgREST Discord/GitHub

**Acceptance Criteria**: All team members comfortable writing PostgreSQL functions

### Risk 5: Rate Limiting Complexity

**Description**: PostgreSQL-based rate limiting may be harder than middleware.

**Likelihood**: Medium
**Impact**: Low

**Mitigation**:
- Implement rate limiting in nginx (simpler approach)
- Alternative: Use PostgreSQL extension like `pg_cron` with custom schema
- Defer rate limiting to Phase 2 if complexity is high

**Acceptance Criteria**: Rate limiting functional by end of Phase 3

---

## Timeline

**Total Duration**: 6 weeks (excluding training)

| Phase | Duration | Start Date | End Date | Key Milestone |
|-------|----------|------------|----------|---------------|
| **Phase 1**: Database Schema Preparation | 2 weeks | Week 1 | Week 2 | ✅ Database migrations complete |
| **Phase 2**: PostgREST Deployment | 1 week | Week 2 | Week 3 | ✅ PostgREST running in production |
| **Phase 3**: Parallel Operation & Testing | 1 week | Week 3 | Week 4 | ✅ Load tests pass |
| **Phase 4**: Client Migration | 1 week | Week 4 | Week 5 | ✅ Zero breaking changes |
| **Phase 5**: FastAPI Deprecation | 1 week | Week 5 | Week 6 | ✅ FastAPI service stopped |

**Note**: Timeline excludes time estimates per requirements. Adjust based on team capacity.

---

## Dependencies

### External Dependencies

- **PostgreSQL Extensions**:
  - `pgcrypto` (password hashing)
  - `pgjwt` (JWT token generation) - [GitHub](https://github.com/michelp/pgjwt)
  - `pg_stat_statements` (query metrics)

- **Infrastructure**:
  - PgBouncer (connection pooling)
  - nginx (reverse proxy)
  - Docker Compose (container orchestration)

- **Monitoring**:
  - Prometheus (metrics collection)
  - Grafana (dashboards)

### Team Dependencies

- **Database Engineer**: Write migrations, stored procedures, RLS policies
- **DevOps Engineer**: Deploy PostgREST, configure nginx, set up monitoring
- **Backend Engineer**: Write integration tests, validate API compatibility
- **Frontend Engineer**: Update Superset dashboards (if needed)

---

## Open Questions

1. **Trino Integration**: Should we migrate Trino queries to PostgreSQL Foreign Data Wrappers, or keep as separate microservice?
   - **Recommendation**: Defer to Phase 2. Focus on PostgreSQL marts first.

2. **Rate Limiting**: Implement in nginx or PostgreSQL?
   - **Recommendation**: Start with nginx for simplicity, explore PostgreSQL-based solution later.

3. **Caching Strategy**: Use HTTP caching, PostgreSQL materialized views, or external cache (Redis)?
   - **Recommendation**: Combination of HTTP `Cache-Control` headers + materialized views.

4. **WebSocket Support**: Do we need real-time features (e.g., live glucose updates)?
   - **Recommendation**: Out of scope for Phase 1. Evaluate Hasura subscriptions if needed.

5. **Custom SQL Endpoint**: How should admins execute custom queries in PostgREST?
   - **Recommendation**: Create `api.execute_sql(query TEXT)` function with strict validation.

---

## Appendix

### A. PostgREST Resources

- **Official Documentation**: https://postgrest.org
- **GitHub Repository**: https://github.com/PostgREST/postgrest
- **Community Discord**: https://discord.gg/postgrest
- **Tutorial**: https://postgrest.org/en/stable/tutorials/tut0.html

### B. PostgreSQL Extensions

- **pgjwt**: https://github.com/michelp/pgjwt
- **pgcrypto**: https://www.postgresql.org/docs/current/pgcrypto.html
- **pgTAP**: https://pgtap.org

### C. Alternative Solutions Considered

| Solution | Pros | Cons | Decision |
|----------|------|------|----------|
| **Hasura GraphQL** | Auto-generates GraphQL, supports subscriptions | Requires GraphQL clients, learning curve | Keep as complementary service |
| **Supabase** | Full backend-as-a-service, includes auth | Opinionated, adds overhead | Too heavy for our use case |
| **Prisma Data Proxy** | Type-safe API, good DX | Requires Node.js, not REST | Not REST-focused |
| **Custom FastAPI Refactor** | Full control | High maintenance | Original problem statement |
| **PostgREST** | ✅ Best fit for requirements | Limited to PostgreSQL | **Selected** |

### D. Example API Calls

**Login:**
```bash
curl -X POST http://localhost:10010/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "analyst123"}'
```

**Get Glucose Readings (with filtering):**
```bash
curl http://localhost:10010/api/v1/glucose/readings?reading_date=gte.2024-01-01&order=reading_date.desc \
  -H "Authorization: Bearer $TOKEN"
```

**Get Statistics:**
```bash
curl http://localhost:10010/api/v1/glucose/statistics?period_days=30 \
  -H "Authorization: Bearer $TOKEN"
```

**Get OpenAPI Spec:**
```bash
curl http://localhost:10010/docs \
  -H "Accept: application/openapi+json"
```

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Manager | _______________ | _______________ | _______ |
| Engineering Lead | _______________ | _______________ | _______ |
| Database Architect | _______________ | _______________ | _______ |
| DevOps Lead | _______________ | _______________ | _______ |

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Next Review**: Post-Phase 1 completion
