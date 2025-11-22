# GitHub Analytics Workflow Guide

This guide explains how to set up and use the GitHub analytics workflow in Phlo, which collects GitHub user events and repository statistics for data analysis and dashboarding.

## Overview

The GitHub workflow follows the same 4-layer architecture as other Phlo workflows:

1. **Ingestion Layer** - Raw data collection from GitHub API
2. **Bronze Layer** - Basic cleaning and type conversion
3. **Silver Layer** - Business logic and enrichment
4. **Gold Layer** - Curated analytics-ready datasets
5. **Marts Layer** - PostgreSQL-optimized dashboard datasets

## Prerequisites

### GitHub API Access

1. **Create a GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a token with appropriate permissions
   - Recommended scopes: `read:user`, `read:org`, `repo` (for private repos)

2. **Environment Configuration**:
   Add to your `.env` file:
   ```bash
   GITHUB_TOKEN=your_github_token_here
   GITHUB_USERNAME=your_github_username
   ```

### Repository Permissions

The workflow collects data for:
- **User Events**: Public events for the configured user
- **Repository Statistics**: Statistics for all repositories owned by the user

For private repositories, ensure your token has appropriate access.

## Architecture Components

### 1. Ingestion Assets (`src/phlo/defs/ingestion/github_assets.py`)

Two main ingestion assets:

#### `github_user_events`
- **Schedule**: Every hour
- **Source**: `GET /users/{username}/events`
- **Data**: User activity events (commits, issues, PRs, etc.)
- **Partitioning**: Daily by event date
- **Storage**: Iceberg `raw.user_events`

#### `github_repo_stats`
- **Schedule**: Daily at 2 AM
- **Source**: `/repos/{owner}/{repo}/stats/*` endpoints
- **Data**: Contributor stats, commit activity, code frequency, participation
- **Partitioning**: Daily by collection date
- **Storage**: Iceberg `raw.repo_stats`

### 2. Data Quality (`src/phlo/defs/quality/github.py`)

Pandera-based schema validation:

#### `github_user_events_quality_check`
- Validates event structure and required fields
- Ensures valid event types and timestamps
- Checks JSON field integrity

#### `github_repo_stats_quality_check`
- Validates repository statistics structure
- Ensures proper data types and ranges
- Verifies JSON statistics format

### 3. Transform Pipeline (dbt models)

#### Bronze Layer (`transforms/dbt/models/bronze/`)
- `stg_github_user_events.sql` - Clean user events staging
- `stg_github_repo_stats.sql` - Clean repository stats staging

#### Silver Layer (`transforms/dbt/models/silver/`)
- `fct_github_user_events.sql` - Enriched events with business logic
  - Event categorization (code_contribution, issue_management, etc.)
  - Time dimensions (hour, day of week)
  - Actor/repo metadata extraction
- `fct_github_repo_stats.sql` - Enriched statistics with metrics
  - Contributor counts and activity scores
  - Commit velocity calculations
  - Repository health indicators

#### Gold Layer (`transforms/dbt/models/gold/`)
- `mrt_github_user_activity.sql` - Curated user activity facts
- `mrt_github_repo_metrics.sql` - Curated repository metrics

#### PostgreSQL Marts (`transforms/dbt/models/marts_postgres/`)
- `mrt_github_activity_overview.sql` - Daily activity summaries
- `mrt_github_repo_insights.sql` - Repository performance analytics

### 4. Publishing (`src/phlo/defs/publishing/trino_to_postgres.py`)

Moves curated marts from Iceberg to PostgreSQL for fast dashboard queries.

## Data Flow

```
GitHub API → DLT Staging → Iceberg Raw → dbt Bronze → dbt Silver → dbt Gold → PostgreSQL Marts
```

## Usage Guide

### 1. Configuration

Ensure your `.env` file includes:
```bash
# GitHub API
GITHUB_TOKEN=ghp_your_token_here
GITHUB_USERNAME=your_github_username
```

### 2. Run Ingestion

Start the Dagster services:
```bash
make up
```

Trigger ingestion manually or wait for schedules:
```bash
# Materialize user events for a specific date
dagster asset materialize --select github_user_events --partition-key 2024-01-15

# Materialize repository stats
dagster asset materialize --select github_repo_stats --partition-key 2024-01-15
```

### 3. Run Transforms

Execute dbt transformations:
```bash
# From the Dagster container
docker exec -it phlo-dagster-dagster-web-1 bash
cd /dbt

# Install dependencies
dbt deps

# Run GitHub models
dbt run --select tag:github

# Run tests
dbt test --select tag:github
```

### 4. Publish to PostgreSQL

Trigger the publishing asset:
```bash
dagster asset materialize --select publish_glucose_marts_to_postgres
```

### 5. Query Results

Connect to PostgreSQL and query the marts:
```sql
-- Activity overview
SELECT * FROM marts.mrt_github_activity_overview
ORDER BY activity_date DESC LIMIT 10;

-- Repository insights
SELECT * FROM marts.mrt_github_repo_insights
WHERE activity_level = 'very_active'
ORDER BY activity_score DESC;
```

## Data Dictionary

### User Events (`mrt_github_user_activity`)

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique GitHub event ID |
| `event_type` | string | GitHub event type (PushEvent, IssuesEvent, etc.) |
| `event_category` | string | Categorized event type (code_contribution, issue_management, etc.) |
| `actor_login` | string | GitHub username of the actor |
| `repo_full_name` | string | Full repository name (owner/repo) |
| `public` | boolean | Whether the event is public |
| `created_at` | timestamp | Event creation timestamp |
| `event_date` | date | Date of the event |
| `hour_of_day` | int | Hour when event occurred (0-23) |

### Repository Metrics (`mrt_github_repo_metrics`)

| Field | Type | Description |
|-------|------|-------------|
| `repo_full_name` | string | Full repository name |
| `contributor_count` | int | Number of contributors |
| `total_commits_last_52_weeks` | int | Total commits in last year |
| `activity_score` | float | Calculated activity score |
| `collection_date` | date | Date statistics were collected |
| `contribution_level` | string | high/medium/low/no contribution |
| `activity_level` | string | very_active/active/moderate/inactive |

### Activity Overview (`mrt_github_activity_overview`)

| Field | Type | Description |
|-------|------|-------------|
| `activity_date` | date | Date of activity |
| `event_count` | int | Total events on this date |
| `unique_repos_count` | int | Number of unique repositories |
| `unique_actors_count` | int | Number of unique actors |
| `code_contribution_events` | int | Number of code contribution events |
| `event_count_7d_avg` | float | 7-day rolling average of events |

## Testing and Quality Assurance

### dbt Tests

The GitHub workflow includes comprehensive dbt tests covering:

- **Schema validation**: Data types, nullability, uniqueness
- **Business rules**: Accepted values, ranges, relationships
- **Data integrity**: Cross-table consistency, referential integrity
- **Custom logic**: Complex business rule validations

#### Running Tests

```bash
# Run all GitHub tests
dbt test --select tag:github

# Run specific layer tests
dbt test --select tag:bronze  # Bronze layer
dbt test --select tag:silver  # Silver layer
dbt test --select tag:gold    # Gold layer
dbt test --select tag:mart    # PostgreSQL marts

# Run specific model tests
dbt test --select stg_github_user_events

# Run with models (build)
dbt build --select tag:github
```

#### Test Categories

- **Bronze**: Basic schema and type validation
- **Silver**: Business logic and enrichment validation
- **Gold**: Curated data integrity and incremental logic
- **Marts**: Dashboard-ready data validation and aggregations

### Quality Checks

Dagster asset checks provide runtime validation:

```bash
# Run quality checks manually
dagster asset check --select github_user_events_quality
dagster asset check --select github_repo_stats_quality
```

## Monitoring and Troubleshooting

### Check Ingestion Status

```sql
-- Check recent user events
SELECT COUNT(*) as event_count,
       DATE(created_at) as event_date
FROM iceberg.raw.user_events
GROUP BY DATE(created_at)
ORDER BY event_date DESC LIMIT 7;
```

### Validate Data Quality

Check Dagster UI for asset check results or run manually:
```bash
dagster asset check --select github_user_events_quality
```

### Common Issues

1. **Rate Limiting**: GitHub API has rate limits (5000/hour for authenticated users)
2. **Missing Data**: Some statistics may return 202 (computing) or 204 (no data)
3. **Token Permissions**: Ensure token has access to private repositories if needed
4. **Date Filtering**: Events are filtered by creation date, not collection date

### Performance Notes

- Repository statistics computation can take time for large repos
- User events are paginated (max 300 events per user)
- Daily partitioning helps manage data volumes
- Incremental updates reduce processing time

## Extending the Workflow

### Adding New Event Types

1. Update `VALID_EVENT_TYPES` in `schemas/github.py`
2. Add new categories in `fct_github_user_events.sql`
3. Update downstream marts as needed

### Adding New Statistics

1. Add new stat collection in `github_assets.py`
2. Update Iceberg schema in `schema.py`
3. Add processing logic in silver layer transforms

### Custom Dashboards

Use the PostgreSQL marts for Superset dashboards:
- Activity trends over time
- Repository health monitoring
- Contributor analytics
- Event type distributions

This workflow provides a solid foundation for GitHub analytics while being easily extensible for additional data sources and metrics.
