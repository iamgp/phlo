# API Layer Configuration

This directory contains automatically generated API views and configurations for exposing glucose data via REST and GraphQL APIs.

## Files

- `views.sql` - PostgreSQL view definitions for PostgREST access
- `hasura-metadata.yaml` - Hasura tracking and permission configuration

## Applying the API Views

### Method 1: Using phlo CLI (Recommended)

```bash
# Generate views from dbt marts (future feature)
phlo api generate-views --models mrt_* --output .phlo/api/views.sql

# Apply views to database
phlo api generate-views --models mrt_* --apply

# Track in Hasura
phlo api hasura track --schema api
phlo api hasura export --output .phlo/api/hasura-metadata.yaml
```

### Method 2: Manual Application

```bash
# Apply views SQL directly to Postgres
psql -h localhost -U postgres -d warehouse -f .phlo/api/views.sql

# Verify views were created
psql -h localhost -U postgres -d warehouse -c "SELECT * FROM api.glucose_overview LIMIT 5;"
```

## Accessing the APIs

### PostgREST (REST API)

Once PostgREST is configured and running, the views are accessible at:

```bash
# Get latest 30 days of glucose overview
curl "http://localhost:3000/api/glucose_overview?select=reading_date,avg_glucose_mg_dl,time_in_range_pct&order=reading_date.desc&limit=30"

# Get hourly patterns
curl "http://localhost:3000/api/hourly_patterns?order=hour_of_day.asc"

# Filter by time in range threshold
curl "http://localhost:3000/api/glucose_overview?time_in_range_pct=gte.70&order=reading_date.desc"

# Get specific date
curl "http://localhost:3000/api/glucose_overview?reading_date=eq.2024-01-15"
```

### Hasura (GraphQL API)

Access the Hasura Console at http://localhost:8080 and run GraphQL queries:

```graphql
query GetRecentGlucoseOverview {
  api_glucose_overview(order_by: { reading_date: desc }, limit: 30) {
    reading_date
    avg_glucose_mg_dl
    time_in_range_pct
    estimated_a1c_pct
    estimated_a1c_7d_avg
  }
}

query GetHourlyPatterns {
  api_hourly_patterns(order_by: { hour_of_day: asc }) {
    hour_of_day
    avg_glucose_mg_dl
    reading_count
    coefficient_of_variation
  }
}

query GetHighVariabilityDays {
  api_glucose_overview(
    where: { coefficient_of_variation: { _gte: 35 } }
    order_by: { reading_date: desc }
  ) {
    reading_date
    avg_glucose_mg_dl
    coefficient_of_variation
    time_in_range_pct
  }
}
```

## View Regeneration

When dbt models change, regenerate the API views:

```bash
# Regenerate views.sql
phlo api generate-views --models mrt_* --output .phlo/api/views.sql

# Review changes
git diff .phlo/api/views.sql

# Apply if changes look good
phlo api generate-views --models mrt_* --apply
```

## Permissions

Views are configured with the following permissions:

- **analyst** role: Read access to all columns
- **admin** role: Full access to all columns
- **anon** role: Disabled by default (uncomment in views.sql to enable)

To modify permissions, edit `views.sql` and reapply.

## Integration with dbt

The dbt mart models are tagged with:

- `api` - Indicates this table should be exposed via API
- `analyst` - Maps to the analyst permission role

To add new models to the API:

1. Tag the dbt model in its YAML file:

   ```yaml
   config:
     tags: ["api", "analyst"]
   ```

2. Regenerate views:

   ```bash
   phlo api generate-views --models mrt_* --apply
   ```

3. Update Hasura tracking:
   ```bash
   phlo api hasura track --schema api
   ```
