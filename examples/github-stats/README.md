# Phlo GitHub Stats Demo

A demo project showing how to build a GitHub activity data lakehouse with Phlo.
Ingests user profile, repository metadata, and user events from GitHub API into an Iceberg lakehouse.

## Why GitHub Stats?

This example demonstrates real-world data engineering patterns:

- **Mixed data types**: Profile snapshots (slowly changing) + events (immutable stream)
- **Different merge strategies**: Shows when to use append vs merge
- **Public API**: Works with GitHub's public API (token optional for higher rate limits)
- **Comprehensive testing**: Includes 367 lines of merge strategy tests
- **Production patterns**: Infrastructure configuration, quality checks, automated testing

## Quick Start

### Standard Mode

```bash
cd examples/github-stats
phlo services init
phlo services start
```

### Development Mode

For developing phlo itself with instant iteration:

```bash
cd examples/github-stats
phlo services init --dev --phlo-source /path/to/phlo
phlo services start
```

This mounts the phlo monorepo into the Dagster container and installs `phlo[defaults]` as an editable install.

### Configure GitHub Access

```bash
# Optional: Set GitHub token for higher rate limits
export GITHUB_TOKEN=your_github_token
export GITHUB_USERNAME=your_username

# Or add to .env
echo "GITHUB_TOKEN=your_token" >> .env
echo "GITHUB_USERNAME=your_username" >> .env
```

## Services

After starting, access:

- **Dagster UI**: http://localhost:3000 - Orchestration & monitoring
- **Trino**: http://localhost:8080 - Query engine
- **MinIO Console**: http://localhost:9001 - Object storage (minio/minio123)
- **Superset**: http://localhost:8088 - BI dashboards (admin/admin)
- **pgweb**: http://localhost:8081 - Database admin

## Project Structure

```
github-stats/
├── .phlo/                      # Infrastructure config
│   └── dagster/                # Dagster workspace
├── workflows/                  # Data workflows
│   ├── ingestion/              # Ingestion assets (@phlo.ingestion)
│   │   └── github/
│   │       ├── user_profile.py # User profile snapshots (merge)
│   │       ├── user_repos.py   # Repository metadata (merge)
│   │       └── user_events.py  # Activity events (append)
│   └── schemas/                # Pandera validation schemas
│       └── github.py           # GitHub data schemas
├── transforms/dbt/             # dbt transformation models
├── tests/                      # Comprehensive test suite
│   └── test_merge_strategies.py  # 367 lines of merge tests
├── phlo.yaml                   # Infrastructure configuration
└── pyproject.toml              # Project dependencies
```

## Data Flow

1. **Ingestion**: Three GitHub data sources with different strategies
   - `user_profile`: User metadata (merge strategy)
   - `user_repos`: Repository data (merge strategy)
   - `user_events`: Activity stream (append strategy)

2. **Bronze**: Raw data validation and staging

3. **Silver**: Cleaned and enriched data

4. **Gold**: Aggregated metrics and analytics

5. **Marts**: BI-ready tables for dashboards

## Merge Strategies Explained

This project demonstrates **both** merge strategies to show when to use each:

### Overview Table

| Workflow         | Strategy | Dedup | Reasoning                      |
| ---------------- | -------- | ----- | ------------------------------ |
| **user_profile** | merge    | last  | Profile data changes over time |
| **user_repos**   | merge    | last  | Repository metadata updates    |
| **user_events**  | append   | hash  | Immutable activity stream      |

### 1. user_profile.py - Merge Strategy

```python
@phlo_ingestion(
    table_name="user_profile",
    unique_key="id",
    merge_strategy="merge",     # Upsert mode
    merge_config={"deduplication_method": "last"},  # Keep latest snapshot
    ...
)
```

**Why merge?**

- User bio, location, company can change
- Follower/following counts update
- Profile pictures change
- Running pipeline multiple times should update existing record

### 2. user_repos.py - Merge Strategy

```python
@phlo_ingestion(
    table_name="user_repos",
    unique_key="id",
    merge_strategy="merge",     # Upsert mode
    merge_config={"deduplication_method": "last"},  # Keep latest metadata
    ...
)
```

**Why merge?**

- Repository descriptions change
- Star and fork counts increase
- Topics and languages update
- Repository settings can change (private/public, archived)

### 3. user_events.py - Append Strategy

```python
@phlo_ingestion(
    table_name="user_events",
    unique_key="id",
    merge_strategy="append",    # Insert-only
    merge_config={"deduplication": True, "deduplication_method": "hash"},
    ...
)
```

**Why append?**

- Events are **immutable** - once created, never change
- High volume activity stream
- Performance matters (no upsert overhead)
- Hash-based deduplication prevents accidental duplicates

**Hash deduplication**: Computes content hash of entire record. If exact duplicate exists (same event ID + content), skip it. This handles idempotency without upsert overhead.

### When to Use Each Strategy

**Use append** when:

- ✅ Data is immutable (logs, events, sensor readings)
- ✅ High volume, performance critical
- ✅ Data never changes once created
- ✅ Example: Server logs, clickstream, activity feeds

**Use merge** when:

- ✅ Data can be updated (user profiles, product catalogs)
- ✅ Need idempotent pipeline runs
- ✅ Data corrections are possible
- ✅ Example: Dimension tables, reference data

### Comparison Table

| Aspect          | Append (events)   | Merge (profile/repos) |
| --------------- | ----------------- | --------------------- |
| **Performance** | Fastest           | Slightly slower       |
| **Idempotency** | Via hash          | Built-in              |
| **Updates**     | Not supported     | Supported             |
| **Use Case**    | Immutable streams | Changing dimensions   |
| **Memory**      | Low               | Higher (dedup)        |

## Infrastructure Configuration

This project includes comprehensive infrastructure configuration in `phlo.yaml`:

```yaml
infrastructure:
  container_naming_pattern: "{project}-{service}-1"

  services:
    dagster_webserver:
      container_name: null
      service_name: dagster-webserver
      host: localhost
      internal_host: dagster-webserver

    postgres:
      container_name: null
      service_name: postgres
      host: localhost
      internal_host: postgres

    # ... (complete service topology)
```

**Benefits:**

- Multi-project deployments on same host
- Consistent service discovery
- Environment-specific configuration
- Production-ready patterns

**Usage:**

```python
from phlo.infrastructure.config import get_service_config

# Get service endpoint
postgres_config = get_service_config("postgres")
endpoint = f"{postgres_config['internal_host']}:{postgres_config['port']}"
```

## Comprehensive Test Suite

This project includes extensive merge strategy tests (`tests/test_merge_strategies.py` - 367 lines):

**Test coverage:**

- Append strategy with hash deduplication
- Merge strategy with last deduplication
- Merge strategy with first deduplication
- Edge cases and error handling
- Performance benchmarks

**Run tests:**

```bash
# All tests
phlo test

# Merge strategy tests only
phlo test tests/test_merge_strategies.py

# With verbose output
phlo test tests/test_merge_strategies.py -v
```

## CLI Commands

### Core Operations

```bash
phlo services start          # Start infrastructure
phlo services stop           # Stop infrastructure
phlo services status         # Check health
phlo materialize <asset>     # Materialize asset
phlo test                    # Run test suite
```

### Asset Materialization

```bash
# Single asset
phlo materialize user_profile --partition 2024-01-15

# Multiple assets
phlo materialize user_profile user_repos user_events

# All GitHub assets
phlo materialize --select "group:github"

# Via Dagster UI
# Navigate to Assets > select asset > Materialize
```

### Monitoring & Debugging

```bash
# View logs
phlo logs --asset user_events
phlo logs --level ERROR --since 1h
phlo logs --follow

# Check lineage
phlo lineage show user_profile
phlo lineage show user_profile --downstream
```

## Real-World Applicability

This example teaches patterns applicable to:

**SaaS Analytics**

- Stripe: transactions (append) + customer profiles (merge)
- Salesforce: activities (append) + account data (merge)
- HubSpot: email events (append) + contact properties (merge)

**Product Analytics**

- Clickstream events (append)
- User profiles (merge)
- Feature flags (merge)

**IoT/Sensor Data**

- Sensor readings (append)
- Device metadata (merge)
- Configuration (merge with hash)

## Learning Path

1. **Start here**: Understand why different merge strategies for different data types
2. **Read the code**: Compare `user_events.py` (append) vs `user_profile.py` (merge)
3. **Run the tests**: See merge strategies in action
4. **Explore phlo.yaml**: Understand infrastructure configuration
5. **Build your own**: Apply patterns to your data sources

## Next Steps

- **Add more data sources**: GitHub issues, pull requests, commits
- **Build dashboards**: Connect Superset to the marts
- **Deploy to production**: Use infrastructure config for multi-environment setup
- **Extend with dbt**: Add silver/gold transformations

## Documentation

- [Phlo Documentation](https://github.com/iamgp/phlo)
- [Developer Guide](../../docs/guides/developer-guide.md) - Comprehensive decorator usage
- [CLI Reference](../../docs/reference/cli-reference.md) - All CLI commands
- [Configuration Reference](../../docs/reference/configuration-reference.md) - Infrastructure config

## Why This Example Matters

Most tutorials show only one ingestion pattern. This example shows:

✅ When to use append vs merge (not just how)
✅ Real API integration with rate limiting
✅ Production infrastructure configuration
✅ Comprehensive test suite
✅ Multiple data types and patterns

Use this as a template for your own data sources.
