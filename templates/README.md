# Phlo Workflow Templates

This directory contains templates for creating common Phlo workflows.

## Quick Start

Copy a template and customize it for your use case:

```bash
# Example: Create a new weather ingestion workflow
cp templates/ingestion/rest_api.py src/phlo/defs/ingestion/weather/observations.py
cp templates/schemas/example_schema.py src/phlo/schemas/weather.py
cp templates/tests/test_ingestion.py tests/test_weather_ingestion.py

# Edit the files and replace TODOs
# Then register the domain in src/phlo/defs/ingestion/__init__.py
```

## Available Templates

### Ingestion Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| **rest_api.py** | REST API ingestion | Third-party APIs (Stripe, GitHub, weather, etc.) |
| **database.py** | Database ingestion | PostgreSQL, MySQL, Snowflake |
| **file.py** | File ingestion | CSV, JSON, Parquet files |

### Schema Templates

| Template | Description |
|----------|-------------|
| **example_schema.py** | Pandera schema template | Define data validation rules |

### Test Templates

| Template | Description |
|----------|-------------|
| **test_ingestion.py** | Ingestion asset tests | Unit tests for ingestion workflows |

## Template Structure

Each template includes:
- ✅ Complete working example
- ✅ Inline comments explaining each part
- ✅ TODO markers for customization points
- ✅ Links to relevant documentation
- ✅ Best practices and common patterns

## Usage Guide

### 1. Choose a Template

Select the template that matches your workflow type:
- REST API ingestion → `templates/ingestion/rest_api.py`
- Database ingestion → `templates/ingestion/database.py`
- File ingestion → `templates/ingestion/file.py`

### 2. Copy and Rename

```bash
# Create domain directory
mkdir -p src/phlo/defs/ingestion/your_domain

# Copy template
cp templates/ingestion/rest_api.py src/phlo/defs/ingestion/your_domain/your_asset.py

# Copy schema template
cp templates/schemas/example_schema.py src/phlo/schemas/your_domain.py
```

### 3. Customize

1. Open the copied files
2. Search for `TODO` comments
3. Replace placeholders with your values:
   - Table names
   - API endpoints
   - Schema fields
   - Unique keys
   - Schedules

### 4. Register Domain

Add import to `src/phlo/defs/ingestion/__init__.py`:

```python
from phlo.defs.ingestion import your_domain  # noqa: F401
```

### 5. Test and Run

```bash
# Restart Dagster
docker restart dagster-webserver

# Materialize in UI
# http://localhost:3000
```

## Best Practices

### Schema Design

1. **Use descriptive field names**: `transaction_amount` not `amt`
2. **Add descriptions**: `pa.Field(description="...")`
3. **Set constraints**: `ge=0, le=100` for percentages
4. **Use appropriate types**: `datetime` for timestamps, `int` for IDs

### Decorator Configuration

1. **Choose unique keys carefully**: Should uniquely identify a record
2. **Set realistic freshness**: Don't alert if data lag is expected
3. **Use cron expressions**: Test at https://crontab.guru
4. **Group logically**: Use domain names (github, stripe, weather)

### Error Handling

1. **Validate early**: Use Pandera schema validation
2. **Fail gracefully**: Let decorator handle retries
3. **Log context**: Decorator logs partition, timing, rows

## Next Steps

After creating your workflow from a template:

1. **Test locally**: See [TESTING_GUIDE.md](../docs/TESTING_GUIDE.md)
2. **Add transformations**: See [DBT_DEVELOPMENT_GUIDE.md](../docs/DBT_DEVELOPMENT_GUIDE.md)
3. **Add quality checks**: See [BEST_PRACTICES_GUIDE.md](../docs/BEST_PRACTICES_GUIDE.md)
4. **Deploy to production**: See [WORKFLOW_DEVELOPMENT_GUIDE.md](../docs/WORKFLOW_DEVELOPMENT_GUIDE.md)

## Getting Help

- **Documentation**: [docs/README.md](../docs/README.md)
- **Full Tutorial**: [WORKFLOW_DEVELOPMENT_GUIDE.md](../docs/WORKFLOW_DEVELOPMENT_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING_GUIDE.md](../docs/TROUBLESHOOTING_GUIDE.md)
- **GitHub Issues**: Report problems or request new templates

## Contributing Templates

Have a useful template? Submit a PR!

1. Create template in appropriate directory
2. Add comprehensive TODO comments
3. Include working example
4. Update this README
5. Add tests if applicable
