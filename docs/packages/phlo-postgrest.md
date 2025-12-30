# phlo-postgrest

PostgREST API service for Phlo.

## Overview

`phlo-postgrest` automatically generates a RESTful API from PostgreSQL schemas. It exposes published tables via REST endpoints.

## Installation

```bash
pip install phlo-postgrest
# or
phlo plugin install postgrest
```

## Profile

Part of the `api` profile.

## Configuration

| Variable            | Default   | Description        |
| ------------------- | --------- | ------------------ |
| `POSTGREST_PORT`    | `3002`    | PostgREST API port |
| `POSTGREST_VERSION` | `v12.2.3` | PostgREST version  |
| `POSTGRES_USER`     | `phlo`    | Database user      |
| `POSTGRES_PASSWORD` | `phlo`    | Database password  |
| `POSTGRES_DB`       | `phlo`    | Database name      |

## Features

### Auto-Configuration

| Feature                 | How It Works                           |
| ----------------------- | -------------------------------------- |
| **Database Connection** | Auto-connects to Phlo's PostgreSQL     |
| **Schema Exposure**     | Exposes `api` and `public` schemas     |
| **Anonymous Role**      | Uses `POSTGRES_USER` as anonymous role |
| **OpenAPI Docs**        | Auto-generates OpenAPI spec            |

## Usage

### Starting the Service

```bash
# Start with API profile
phlo services start --profile api

# Or start individually
phlo services start --service postgrest
```

### API Examples

```bash
# Get OpenAPI spec
curl http://localhost:3002/

# List all rows from a table
curl http://localhost:3002/mrt_daily_summary

# Filter rows
curl "http://localhost:3002/mrt_daily_summary?date=gte.2024-01-01"

# Pagination
curl "http://localhost:3002/mrt_daily_summary?limit=10&offset=20"

# Sorting
curl "http://localhost:3002/mrt_daily_summary?order=date.desc"

# Select specific columns
curl "http://localhost:3002/mrt_daily_summary?select=date,total_count"
```

### Filter Operators

| Operator | Description              | Example                   |
| -------- | ------------------------ | ------------------------- |
| `eq`     | Equal                    | `?column=eq.value`        |
| `neq`    | Not equal                | `?column=neq.value`       |
| `gt`     | Greater than             | `?column=gt.100`          |
| `gte`    | Greater or equal         | `?column=gte.100`         |
| `lt`     | Less than                | `?column=lt.100`          |
| `lte`    | Less or equal            | `?column=lte.100`         |
| `like`   | Pattern match            | `?column=like.*pattern*`  |
| `ilike`  | Case-insensitive pattern | `?column=ilike.*pattern*` |
| `in`     | In list                  | `?column=in.(a,b,c)`      |
| `is`     | Is null/true/false       | `?column=is.null`         |

## Endpoints

| Endpoint         | URL                      |
| ---------------- | ------------------------ |
| **API Base**     | `http://localhost:3002`  |
| **OpenAPI Spec** | `http://localhost:3002/` |

## Entry Points

| Entry Point             | Plugin                   |
| ----------------------- | ------------------------ |
| `phlo.plugins.services` | `PostgrestServicePlugin` |
| `phlo.plugins.cli`      | PostgREST CLI commands   |

## Related Packages

- [phlo-postgres](phlo-postgres.md) - Database service
- [phlo-hasura](phlo-hasura.md) - GraphQL alternative
- [phlo-api](phlo-api.md) - Custom API endpoints

## Next Steps

- [PostgREST Setup](../setup/postgrest.md) - Complete configuration
- [API Reference](../reference/api.md) - API documentation
