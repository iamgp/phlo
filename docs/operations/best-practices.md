# Best Practices Guide

## Building Production-Ready Data Pipelines

This guide contains battle-tested best practices for building reliable, maintainable, and scalable data pipelines in Phlo.

---

## Table of Contents

1. [General Principles](#general-principles)
2. [Code Organization](#code-organization)
3. [Data Quality](#data-quality)
4. [Performance](#performance)
5. [Security](#security)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [Git Workflow](#git-workflow)
10. [Production Deployment](#production-deployment)

---

## General Principles

### 1. Idempotency

**Make operations repeatable without side effects.**

```python
# BAD: Not idempotent
@dg.asset
def append_data():
    data = fetch_data()
    append_to_table(data)  # Running twice appends twice!

# GOOD: Idempotent
@dg.asset
def upsert_data():
    data = fetch_data()
    upsert_to_table(data, unique_key='id')  # Running twice has same result
```

**Benefits:**
- Safe to retry on failure
- Can backfill without duplicates
- Predictable behavior

### 2. Immutability

**Don't modify existing data, create new versions.**

```sql
-- BAD: Updates in place
UPDATE orders SET status = 'shipped' WHERE order_id = 123

-- GOOD: Append new record with updated status
INSERT INTO orders_history
SELECT *, CURRENT_TIMESTAMP as updated_at
FROM orders WHERE order_id = 123
```

**Benefits:**
- Time travel (see historical state)
- Audit trail (who changed what when)
- Easier to debug issues

### 3. Fail Fast

**Detect problems early, fail clearly.**

```python
# GOOD: Validate inputs immediately
@dg.asset
def process_data():
    data = fetch_data()

    # Fail fast if data is bad
    assert len(data) > 0, "No data fetched"
    assert 'id' in data.columns, "Missing required column: id"
    assert data['id'].is_unique, "Duplicate IDs found"

    # Now process with confidence
    return transform(data)
```

### 4. Single Responsibility

**Each asset/model should do one thing well.**

```python
# BAD: Does too much
@dg.asset
def fetch_transform_and_load_everything():
    # Fetches from 5 APIs
    # Transforms data
    # Loads to 3 destinations
    # Too complex!

# GOOD: Separate responsibilities
@dg.asset
def fetch_orders():
    return fetch_from_api('orders')

@dg.asset
def transform_orders(fetch_orders):
    return transform(fetch_orders)

@dg.asset
def load_orders(transform_orders):
    load_to_warehouse(transform_orders)
```

### 5. Explicit Dependencies

**Make dependencies clear and explicit.**

```python
# BAD: Hidden dependency
@dg.asset
def downstream():
    # Implicitly depends on upstream table existing
    return query("SELECT * FROM upstream_table")

# GOOD: Explicit dependency
@dg.asset
def downstream(upstream):  # Clear dependency
    return transform(upstream)
```

---

## Code Organization

### File Structure

```
src/phlo/
├── config.py                    # Central configuration
├── definitions.py               # Main entry point
│
├── defs/                        # Modular definitions
│   ├── ingestion/
│   │   ├── __init__.py          # Exports build_ingestion_defs()
│   │   ├── api_assets.py        # API ingestion
│   │   └── file_assets.py       # File ingestion
│   │
│   ├── transform/
│   │   └── dbt.py               # dbt integration
│   │
│   ├── quality/
│   │   ├── __init__.py
│   │   └── checks.py            # Data quality checks
│   │
│   └── resources/
│       ├── __init__.py
│       ├── trino.py             # Trino resource
│       └── iceberg.py           # Iceberg resource
│
├── schemas/                     # Pandera schemas
│   ├── orders.py
│   └── customers.py
│
└── utils/                       # Shared utilities
    ├── dates.py
    └── transformations.py
```

### Naming Conventions

**Assets:**
```
<action>_<subject>_<detail>

Examples:
- fetch_orders_api
- transform_orders_silver
- aggregate_orders_daily
- publish_orders_postgres
```

**dbt Models:**
```
stg_<source>_<entity>           # Bronze
fct_<subject>_<grain>           # Silver facts
dim_<entity>                    # Silver dimensions
agg_<grain>_<subject>           # Gold aggregations
mrt_<audience>_<subject>        # Marts
```

**Python Functions:**
```python
# Use verbs for functions
def fetch_data()
def transform_records()
def calculate_metrics()

# Use nouns for classes
class TrinoResource
class OrderSchema
class DateUtils
```

### Configuration Management

**Use environment variables:**

```python
# config.py
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # API
    API_KEY: str
    API_BASE_URL: str = "https://api.example.com"

    # Feature flags
    ENABLE_NOTIFICATIONS: bool = False
    ENABLE_CACHING: bool = True

    class Config:
        env_file = ".env"
```

**Benefits:**
- One place to change configuration
- Easy to switch between environments
- Secrets not in code

---

## Data Quality

### Add Schema Validation

**Use Pandera:**

```python
import pandera as pa

class OrderSchema(pa.DataFrameModel):
    order_id: Series[str] = pa.Field(unique=True)
    customer_id: Series[str] = pa.Field()
    amount: Series[float] = pa.Field(ge=0)  # >= 0
    order_date: Series[datetime] = pa.Field()

    @pa.check("amount")
    def check_reasonable_amount(cls, amount: Series[float]) -> Series[bool]:
        """Amounts should be reasonable (< $10,000)."""
        return amount < 10000

@dg.asset
def validated_orders() -> pandera_schema_to_dagster_type(OrderSchema):
    data = fetch_orders()
    return data  # Automatically validated!
```

### Add dbt Tests

**Test everything important:**

```yaml
models:
  - name: fct_orders
    tests:
      - dbt_utils.at_least_one  # Table not empty

    columns:
      - name: order_id
        tests:
          - not_null
          - unique

      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id

      - name: amount
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1000000
```

### Add Asset Checks

```python
from dagster import asset_check, AssetCheckResult

@asset_check(asset=orders)
def check_orders_recent(orders):
    """Ensure we have recent orders."""
    max_date = orders['order_date'].max()
    age_hours = (datetime.now() - max_date).total_seconds() / 3600

    if age_hours > 24:
        return AssetCheckResult(
            passed=False,
            description=f"Most recent order is {age_hours:.1f} hours old"
        )

    return AssetCheckResult(passed=True)
```

### Implement Data Contracts

**Define expectations:**

```yaml
# data_contracts/orders.yml
table: raw.orders
owner: data-team@company.com
description: Customer orders from e-commerce platform

schema:
  - name: order_id
    type: string
    required: true
    unique: true

  - name: amount
    type: decimal(10,2)
    required: true
    constraints:
      - min: 0
      - max: 1000000

freshness:
  warn_threshold: 2h
  error_threshold: 24h
```

---

## Performance

### Partition Large Datasets

```python
from dagster import DailyPartitionsDefinition

daily = DailyPartitionsDefinition(start_date="2024-01-01")

@dg.asset(partitions_def=daily)
def daily_orders(context):
    date = context.partition_key
    # Process only one day
    return fetch_orders_for_date(date)
```

### Use Incremental dbt Models

```sql
{{
    config(
        materialized='incremental',
        unique_key='order_id',
    )
}}

SELECT * FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

### Optimize Queries

```sql
-- BAD: Full table scan
SELECT *
FROM orders
WHERE YEAR(order_date) = 2024

-- GOOD: Partition pruning
SELECT *
FROM orders
WHERE order_date >= '2024-01-01'
  AND order_date < '2025-01-01'

-- BETTER: Add LIMIT for exploration
SELECT *
FROM orders
WHERE order_date >= '2024-01-01'
LIMIT 10000
```

### Cache Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_api_client():
    """Cached API client (created once)."""
    return ExpensiveAPIClient()

@dg.asset
def fetch_data():
    client = get_api_client()  # Reuses cached client
    return client.fetch()
```

### Parallelize When Possible

```python
# BAD: Sequential
@dg.asset
def process_all_cities():
    results = []
    for city in cities:
        results.append(process_city(city))  # One at a time
    return results

# GOOD: Parallel (with static partitions)
city_partition = StaticPartitionsDefinition(cities)

@dg.asset(partitions_def=city_partition)
def process_city(context):
    city = context.partition_key
    return process_city(city)  # Each city processes in parallel!
```

---

## Security

### Never Commit Secrets

**.gitignore:**
```
.env
*.key
*.pem
secrets/
credentials.json
```

**Use environment variables:**
```python
# GOOD
API_KEY = os.getenv('API_KEY')

# BAD
API_KEY = 'abc123'  # Don't hardcode!
```

### Use Strong Authentication

```python
from phlo.config import get_config

@dg.asset
def fetch_from_api():
    config = get_config()

    # Use API key from environment
    headers = {
        'Authorization': f'Bearer {config.API_KEY}'
    }

    response = requests.get(config.API_URL, headers=headers)
    return response.json()
```

### Limit Access

```sql
-- Create read-only user for analysts
CREATE USER analyst_user WITH PASSWORD 'secure_password';
GRANT USAGE ON SCHEMA marts TO analyst_user;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO analyst_user;

-- Don't grant access to raw data
REVOKE ALL ON SCHEMA raw FROM analyst_user;
```

### Encrypt Sensitive Data

```python
from cryptography.fernet import Fernet

def encrypt_sensitive_field(value: str, key: bytes) -> str:
    """Encrypt sensitive data before storing."""
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()

@dg.asset
def process_customer_data():
    data = fetch_customers()

    # Encrypt email addresses
    encryption_key = get_config().ENCRYPTION_KEY
    data['email_encrypted'] = data['email'].apply(
        lambda x: encrypt_sensitive_field(x, encryption_key)
    )

    # Drop plaintext email
    data = data.drop(columns=['email'])

    return data
```

---

## Monitoring and Observability

### Add Logging

```python
@dg.asset
def process_orders(context: dg.AssetExecutionContext):
    context.log.info("Starting order processing")

    orders = fetch_orders()
    context.log.info(f"Fetched {len(orders)} orders")

    # Log important metrics
    total_amount = orders['amount'].sum()
    context.log.info(f"Total order value: ${total_amount:,.2f}")

    # Log warnings
    late_orders = orders[orders['is_late']]
    if len(late_orders) > 10:
        context.log.warning(f"{len(late_orders)} orders are late!")

    return orders
```

### Return Metadata

```python
@dg.asset
def process_orders(context) -> dg.MaterializeResult:
    orders = fetch_orders()

    return dg.MaterializeResult(
        metadata={
            "num_records": len(orders),
            "date_range": f"{orders['date'].min()} to {orders['date'].max()}",
            "total_amount": dg.MetadataValue.float(orders['amount'].sum()),
            "preview": dg.MetadataValue.md(orders.head().to_markdown()),
        }
    )
```

### Set Up Alerts

**Dagster sensors:**

```python
@dg.sensor(
    name="alert_on_failure",
    minimum_interval_seconds=60,
)
def failure_alert_sensor(context):
    """Alert on asset failures."""
    runs = context.instance.get_runs(
        filters=dg.RunsFilter(
            statuses=[dg.DagsterRunStatus.FAILURE],
            created_after=datetime.now() - timedelta(minutes=5),
        )
    )

    for run in runs:
        send_alert(f"Run {run.run_id} failed: {run.pipeline_name}")
```

**dbt tests as monitors:**

```yaml
models:
  - name: fct_orders
    tests:
      - dbt_utils.recency:
          datepart: hour
          field: created_at
          interval: 2
          # Alerts if no orders in last 2 hours
```

### Use Grafana Dashboards

Monitor key metrics:
- Asset materialization rates
- Test pass/fail rates
- Query performance
- Resource usage
- Data volumes

---

## Testing

### Unit Tests

```python
# tests/test_transformations.py
import pytest
from phlo.utils.transformations import calculate_tax

def test_calculate_tax():
    assert calculate_tax(100, 0.1) == 10
    assert calculate_tax(0, 0.1) == 0
    assert calculate_tax(100, 0) == 0

def test_calculate_tax_negative():
    with pytest.raises(ValueError):
        calculate_tax(-100, 0.1)
```

### Integration Tests

```python
# tests/test_pipeline.py
from dagster import materialize
from phlo.definitions import defs

def test_orders_pipeline():
    """Test complete orders pipeline."""

    # Materialize all orders assets
    result = materialize(
        defs.get_asset_graph().get_all_asset_keys(),
        selection=dg.AssetSelection.groups("orders"),
    )

    assert result.success
```

### dbt Tests

```sql
-- tests/assert_no_negative_amounts.sql
SELECT *
FROM {{ ref('fct_orders') }}
WHERE amount < 0
```

### Test in CI/CD

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/

      - name: Run dbt tests
        run: dbt test --project-dir transforms/dbt
```

---

## Documentation

### Document Assets

```python
@dg.asset(
    name="customer_lifetime_value",
    description="""
    Calculates customer lifetime value (LTV) based on historical orders.

    **Calculation:**
    - LTV = SUM(order_amount) for all completed orders

    **Business Rules:**
    - Only includes orders with status = 'completed'
    - Excludes returns and refunds
    - Updated daily

    **Depends On:**
    - fct_orders (silver layer)
    - dim_customers (silver layer)

    **Used By:**
    - mrt_customer_segmentation
    - Executive dashboard (Superset)

    **Owner:** Data Team (data-team@company.com)
    """,
    group_name="customer_analytics",
    compute_kind="python",
)
def customer_lifetime_value(fct_orders, dim_customers):
    ...
```

### Document dbt Models

```yaml
# models/silver/schema.yml
models:
  - name: fct_orders
    description: |
      Orders with calculated metrics and business logic.

      ## Business Rules
      - Excludes cancelled orders
      - Applies 10% tax rate
      - Free shipping for orders > $100

      ## Data Quality
      - Deduplicated on order_id
      - Late-arriving data handled via incremental logic

      ## Refresh Schedule
      - Incremental: Hourly
      - Full refresh: Weekly (Sunday 2 AM)

      ## Owner
      Data Engineering Team

    columns:
      - name: order_id
        description: Unique order identifier (UUID)
        tests:
          - not_null
          - unique
```

### Generate Documentation

```bash
# dbt documentation
dbt docs generate
dbt docs serve

# Dagster documentation
# Available in UI automatically!
```

### Maintain README

```markdown
# Phlo Data Platform

## Quick Start
...

## Architecture
...

## Common Workflows
...

## Troubleshooting
...

## Contact
For help: data-team@company.com
```

---

## Git Workflow

### Branching Strategy

```
main (production)
  ├─ dev (staging)
  │   ├─ feature/add-customer-segmentation
  │   ├─ fix/orders-duplicate-bug
  │   └─ refactor/optimize-queries
```

### Commit Messages

```bash
# Good commit messages
git commit -m "feat: add customer lifetime value calculation"
git commit -m "fix: resolve duplicate orders in fct_orders"
git commit -m "docs: update data modeling guide"
git commit -m "perf: optimize daily aggregation query"
git commit -m "test: add validation for negative amounts"

# Bad commit messages
git commit -m "updates"
git commit -m "fix bug"
git commit -m "wip"
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push and create PR**
   ```bash
   git push -u origin feature/my-feature
   ```

4. **PR template:**
   ```markdown
   ## What
   Brief description of changes

   ## Why
   Why are these changes needed?

   ## Testing
   - [ ] Unit tests pass
   - [ ] dbt tests pass
   - [ ] Manually tested in dev

   ## Screenshots
   (if applicable)
   ```

5. **Code review**

6. **Merge to dev, test, then merge to main**

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Secrets configured
- [ ] Monitoring set up
- [ ] Rollback plan documented

### Deployment Strategy

**1. Test in dev environment**
```bash
# Deploy to dev
git checkout dev
git pull origin main
git push origin dev

# Monitor in Dagster dev environment
```

**2. Smoke test**
```bash
# Materialize critical assets
dagster asset materialize -a critical_asset_1
dagster asset materialize -a critical_asset_2

# Run dbt tests
dbt test --select tag:critical
```

**3. Deploy to production**
```bash
# Merge to main
git checkout main
git merge dev
git push origin main

# Deployment happens automatically (CI/CD)
```

**4. Monitor**
- Check Grafana dashboards
- Watch Dagster runs
- Check alert channels

### Rollback Plan

```bash
# If something goes wrong, revert
git revert <commit-hash>
git push origin main

# Or roll back to previous version
git reset --hard <previous-commit>
git push --force origin main

# Restore data from Nessie/Iceberg
# Time travel to before deployment
SELECT * FROM iceberg.silver.fct_orders
FOR SYSTEM_TIME AS OF TIMESTAMP '2024-11-05 10:00:00';
```

---

## Summary

**Key Principles:**
- ✅ Idempotency
- ✅ Immutability
- ✅ Fail fast
- ✅ Single responsibility
- ✅ Explicit dependencies

**Code Quality:**
- ✅ Clear naming
- ✅ Modular structure
- ✅ Configuration management
- ✅ Error handling

**Data Quality:**
- ✅ Schema validation
- ✅ dbt tests
- ✅ Asset checks
- ✅ Data contracts

**Operations:**
- ✅ Monitoring
- ✅ Logging
- ✅ Alerting
- ✅ Testing
- ✅ Documentation

**Security:**
- ✅ No secrets in code
- ✅ Strong authentication
- ✅ Least privilege access
- ✅ Encrypt sensitive data

**Deployment:**
- ✅ Version control
- ✅ Code review
- ✅ Testing in dev
- ✅ Gradual rollout
- ✅ Monitoring
- ✅ Rollback plan

---

**Remember:** Good practices prevent problems before they happen. Invest time upfront to save time later!
