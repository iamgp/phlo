# Hasura GraphQL Setup Guide

Step-by-step guide to configuring Hasura for the Cascade lakehouse.

## Overview

Hasura auto-generates a GraphQL API from your Postgres `marts` schema, providing:
- Instant GraphQL queries and mutations
- Real-time subscriptions
- Role-based permissions
- GraphQL playground/explorer

## Quick Start

```bash
# Start Hasura (requires Postgres running)
make up-api

# Open Hasura console
make hasura
# Or: http://localhost:8081/console
```

**Admin Secret:** `cascade-admin-secret-change-me` (set in `.env`)

---

## Initial Setup

### 1. Track Postgres Tables

Hasura needs to "track" tables to generate GraphQL schema.

1. Open Hasura console: http://localhost:8081/console
2. Navigate to **Data** tab
3. Click **public** schema (or marts if you have it)
4. You'll see available tables:
   - `mrt_glucose_overview`
   - `mrt_glucose_hourly_patterns`
5. Click **Track** for each table you want to expose
6. Click **Track All** to track all foreign keys/relationships

**Result:** GraphQL types are now generated for each table.

---

### 2. Configure Permissions

By default, tracked tables have NO permissions. You must configure access.

#### Configure `admin` Role

1. Click on `mrt_glucose_overview` table
2. Go to **Permissions** tab
3. Click **Enter new role** → type `admin`
4. Click **select** column
5. Configure permissions:
   - **Row select permissions:** `Without any checks` (full access)
   - **Column select permissions:** Check all columns
   - **Aggregation queries permissions:** Enable
6. Click **Save Permissions**
7. Repeat for **insert**, **update**, **delete** if needed (usually not for marts)

#### Configure `analyst` Role

1. Click **Enter new role** → type `analyst`
2. Click **select** column
3. Configure permissions:
   - **Row select permissions:** `Without any checks` (read-only, full access)
   - **Column select permissions:** Check all columns
   - **Aggregation queries permissions:** Enable
4. Click **Save Permissions**
5. **DO NOT** enable insert/update/delete (analyst is read-only)

#### Repeat for All Tables

Repeat the above for:
- `mrt_glucose_hourly_patterns`
- Any other marts tables

---

### 3. Test GraphQL Queries

1. Navigate to **API** tab (GraphiQL explorer)
2. You'll see GraphQL schema in the right sidebar
3. Try a query:

```graphql
query GetGlucoseReadings {
  mrt_glucose_overview(limit: 10, order_by: {date: desc}) {
    date
    avg_glucose
    min_glucose
    max_glucose
    readings_count
  }
}
```

4. Click **Play** button
5. You should see results from your Postgres `marts` schema

---

### 4. Set Request Headers

For authenticated requests:

1. In GraphiQL, click **Request Headers** at bottom
2. Add JWT token:

```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"
}
```

3. Get token from FastAPI login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

4. Copy `access_token` from response
5. Paste into GraphiQL header
6. Run authenticated queries

---

## Advanced Configuration

### Custom Views

Create views in Postgres for common queries, then track them in Hasura.

**Example:**
```sql
CREATE VIEW marts.v_recent_readings AS
SELECT *
FROM marts.mrt_glucose_overview
WHERE date >= CURRENT_DATE - INTERVAL '30 days';
```

Then track `v_recent_readings` in Hasura console.

---

### Relationships

If you have foreign keys between tables, Hasura can auto-track relationships.

**Example:** If you add a `user_id` column to marts tables:

1. Create foreign key in Postgres:
```sql
ALTER TABLE marts.mrt_glucose_overview
ADD COLUMN user_id TEXT REFERENCES users(id);
```

2. In Hasura console → **Data** → Track relationship
3. Hasura generates nested queries:

```graphql
query GetUserWithReadings {
  users {
    id
    name
    glucose_readings {  # Auto-generated relationship
      date
      avg_glucose
    }
  }
}
```

---

### Computed Fields

Add server-side computed values to GraphQL responses.

**Example:** Create Postgres function:

```sql
CREATE FUNCTION marts.glucose_status(mrt_glucose_overview_row marts.mrt_glucose_overview)
RETURNS TEXT AS $$
  SELECT CASE
    WHEN mrt_glucose_overview_row.avg_glucose < 70 THEN 'low'
    WHEN mrt_glucose_overview_row.avg_glucose > 180 THEN 'high'
    ELSE 'normal'
  END;
$$ LANGUAGE SQL STABLE;
```

Add computed field in Hasura:
1. **Data** → `mrt_glucose_overview` → **Modify** tab
2. **Add a computed field**
3. Function: `glucose_status`
4. Save

Query with computed field:
```graphql
query {
  mrt_glucose_overview {
    date
    avg_glucose
    status  # Computed field
  }
}
```

---

### Row-Level Security

Restrict data access based on JWT claims.

**Example:** Only show data for authenticated user:

1. Add `user_id` column to tables
2. In permissions for `analyst` role:
   - **Row select permissions:** Custom check
   - Enter condition:
   ```json
   {
     "user_id": {
       "_eq": "X-Hasura-User-Id"
     }
   }
   ```
3. Save

Now analysts only see rows where `user_id` matches their JWT token's `user_id` claim.

---

### Actions (Custom Business Logic)

Call external REST endpoints from GraphQL.

**Example:** Trigger data refresh:

1. **Actions** tab → **Create**
2. Define action:

```graphql
type Mutation {
  refreshGlucoseData: RefreshResponse
}

type RefreshResponse {
  success: Boolean!
  message: String!
}
```

3. Handler: `http://api:8000/api/v1/admin/refresh`
4. Add custom headers (JWT token forwarding)
5. Save

Query:
```graphql
mutation {
  refreshGlucoseData {
    success
    message
  }
}
```

---

### Event Triggers

Run webhooks when data changes.

**Example:** Send alert when glucose reading is high:

1. **Events** tab → **Create Event Trigger**
2. Table: `mrt_glucose_overview`
3. Operations: Insert, Update
4. Webhook: `http://api:8000/api/v1/webhooks/glucose-alert`
5. Add condition:
```json
{
  "avg_glucose": {
    "_gt": 180
  }
}
```
6. Save

Hasura will POST to webhook when condition matches.

---

### Subscriptions

Real-time data via WebSockets.

**Example subscription:**
```graphql
subscription WatchGlucose {
  mrt_glucose_overview(
    limit: 1
    order_by: {date: desc}
  ) {
    date
    avg_glucose
  }
}
```

Client will receive updates when data changes.

**JavaScript client:**
```javascript
import { createClient } from 'graphql-ws';

const client = createClient({
  url: 'ws://localhost:8081/v1/graphql',
  connectionParams: {
    headers: {
      Authorization: 'Bearer YOUR_TOKEN'
    }
  }
});

client.subscribe(
  {
    query: `subscription { mrt_glucose_overview(limit: 1, order_by: {date: desc}) { date avg_glucose } }`
  },
  {
    next: (data) => console.log('Update:', data),
    error: (error) => console.error('Error:', error),
    complete: () => console.log('Done')
  }
);
```

---

## Metadata Management

### Export Metadata

Save Hasura configuration to version control:

```bash
# Install Hasura CLI
npm install --global hasura-cli

# Export metadata
cd /path/to/cascade
hasura metadata export \
  --endpoint http://localhost:8081 \
  --admin-secret cascade-admin-secret-change-me
```

Creates `metadata/` directory with:
- Tables tracking
- Permissions
- Relationships
- Actions
- Event triggers

**Commit to git** for reproducible setup.

---

### Apply Metadata

Restore configuration to new Hasura instance:

```bash
hasura metadata apply \
  --endpoint http://localhost:8081 \
  --admin-secret cascade-admin-secret-change-me
```

Useful for:
- Development → Production deployment
- Team collaboration
- Disaster recovery

---

### Migrations

Track database schema changes:

```bash
# Initialize
hasura init hasura-project --endpoint http://localhost:8081

# Create migration
hasura migrate create add_user_column \
  --sql-from-server \
  --database-name default

# Apply migration
hasura migrate apply
```

Keeps database schema and Hasura metadata in sync.

---

## Security Hardening

### Production Checklist

- [ ] **Change admin secret** - Update `HASURA_ADMIN_SECRET` in `.env`
- [ ] **Disable dev mode** - Set `HASURA_GRAPHQL_DEV_MODE=false`
- [ ] **Disable console** - Set `HASURA_GRAPHQL_ENABLE_CONSOLE=false` (use CLI)
- [ ] **Restrict CORS** - Set specific origins in `HASURA_GRAPHQL_CORS_DOMAIN`
- [ ] **Enable HTTPS** - Use reverse proxy (nginx/Caddy)
- [ ] **Add rate limiting** - Configure at reverse proxy level
- [ ] **Audit permissions** - Review all role permissions regularly
- [ ] **Monitor logs** - Enable all log types for audit trail

---

### JWT Configuration

Hasura validates JWT tokens using shared secret with FastAPI.

**Current config** (in docker-compose.yml):
```yaml
HASURA_GRAPHQL_JWT_SECRET: '{"type":"HS256","key":"${JWT_SECRET}"}'
```

**JWT payload structure:**
```json
{
  "sub": "admin",
  "user_id": "admin_001",
  "email": "admin@cascade.local",
  "role": "admin",
  "exp": 1234567890,
  "https://hasura.io/jwt/claims": {
    "x-hasura-allowed-roles": ["admin"],
    "x-hasura-default-role": "admin",
    "x-hasura-user-id": "admin_001"
  }
}
```

Hasura reads `x-hasura-*` claims for permission checks.

---

## Troubleshooting

### Tables Not Showing

**Issue:** Tables not appearing in Hasura console

**Solutions:**
1. Verify Postgres connection: Check `HASURA_GRAPHQL_DATABASE_URL` in docker-compose.yml
2. Check schema: Ensure tables are in correct schema (`marts` or `public`)
3. Reload metadata: **Data** tab → gear icon → **Reload**
4. Check Postgres logs: `docker compose logs postgres`

---

### Permission Denied Errors

**Issue:** GraphQL query returns permission denied

**Solutions:**
1. Check role in JWT token matches configured role (`admin` or `analyst`)
2. Verify permissions set for that role in Hasura console
3. Check row-level security conditions
4. Test with admin secret header instead of JWT to verify table access

---

### Slow Queries

**Issue:** GraphQL queries taking too long

**Solutions:**
1. Add indexes to Postgres tables:
```sql
CREATE INDEX idx_glucose_date ON marts.mrt_glucose_overview(date);
```
2. Limit query depth in Hasura settings
3. Use pagination with `limit` and `offset`
4. Enable query caching (requires Hasura Pro)
5. Use FastAPI for heavy analytics queries instead

---

### JWT Validation Failures

**Issue:** `JWTInvalid` or `JWTExpired` errors

**Solutions:**
1. Verify JWT secret matches between FastAPI and Hasura:
```bash
docker compose exec api env | grep JWT_SECRET
docker compose exec hasura env | grep JWT_SECRET
```
2. Check token expiration (default 60 minutes)
3. Verify token format in request header: `Bearer YOUR_TOKEN`
4. Test token at https://jwt.io (paste token, verify signature with secret)

---

## GraphQL Best Practices

### Pagination

Always paginate large result sets:

```graphql
query GetReadingsPaginated($limit: Int!, $offset: Int!) {
  mrt_glucose_overview(
    limit: $limit
    offset: $offset
    order_by: {date: desc}
  ) {
    date
    avg_glucose
  }
}
```

### Aggregations

Use aggregation queries for summaries:

```graphql
query GetStats {
  mrt_glucose_overview_aggregate {
    aggregate {
      count
      avg { avg_glucose }
      max { max_glucose }
      min { min_glucose }
    }
  }
}
```

### Query Naming

Always name your queries:

```graphql
# Good
query GetGlucoseReadings { ... }

# Bad (anonymous)
query { ... }
```

Helps with debugging and monitoring.

---

## Resources

- [Hasura Docs](https://hasura.io/docs/latest/index/)
- [GraphQL Spec](https://spec.graphql.org/)
- [Hasura CLI](https://hasura.io/docs/latest/hasura-cli/overview/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)

---

## Next Steps

1. **Track all marts tables** in Hasura console
2. **Configure permissions** for admin and analyst roles
3. **Test queries** in GraphiQL playground
4. **Export metadata** for version control
5. **Integrate with frontend** using Apollo Client or similar
6. **Set up monitoring** via Hasura logs

For API usage examples, see [API Reference](../reference/api.md).
