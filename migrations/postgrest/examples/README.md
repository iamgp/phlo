# PostgREST API Examples

This directory contains **example** SQL files showing how to create domain-specific API views and functions for PostgREST.

## ⚠️ Important

These are **examples only** - they are specific to the glucose monitoring use case and should **NOT** be run as part of the core Phlo setup.

## What's Here

### `004_api_schema.sql` - Example API Views

Shows how to create views in the `api` schema that expose your mart data:

```sql
CREATE VIEW api.glucose_readings AS
SELECT * FROM marts.mrt_glucose_overview;
```

**Your workflow:** Create similar views for YOUR data based on YOUR marts/tables.

### `005_api_functions.sql` - Example API Functions

Shows how to create PostgreSQL functions for computed endpoints:

```sql
CREATE FUNCTION api.glucose_statistics(period_days INT)
RETURNS JSON AS $$
-- Calculate statistics...
$$ LANGUAGE plpgsql;
```

**Your workflow:** Create similar functions for YOUR business logic.

## How to Use These

1. **Don't copy blindly** - These are glucose-specific examples
2. **Adapt for your data** - Create views/functions for your domain
3. **Put in your project** - Not in the Phlo package
4. **Use dbt if you want** - Or plain SQL files, your choice

## Core Phlo Infrastructure

The core PostgREST authentication infrastructure (auth schema, JWT, roles) is installed via:

```bash
phlo api setup-postgrest
```

That command does **NOT** create these example views - only the auth infrastructure.
