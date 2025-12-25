# dbt Tests for GitHub Analytics

This directory contains comprehensive tests for the GitHub analytics workflow in Phlo.

## Test Coverage

### Schema Tests (YAML-based)

- **Column-level tests**: Not null, unique, accepted values, data types
- **Referential integrity**: Foreign key relationships
- **Business rules**: Valid ranges, classifications, and categorizations

### Custom Tests (SQL-based)

- **Data integrity**: Cross-table consistency checks
- **Business logic**: Complex validation rules
- **Trend analysis**: Time-series validation

## Test Categories

### 1. Bronze Layer Tests (`models/bronze/*.yml`)

- Basic schema validation for staging tables
- Data type and nullability checks
- Accepted values for categorical fields

### 2. Silver Layer Tests (`models/silver/*.yml`)

- Fact table integrity
- Business logic validation
- Relationship testing
- Type-specific validations

### 3. Gold Layer Tests (`models/gold/*.yml`)

- Curated data quality
- Incremental logic validation
- Business rule enforcement

### 4. Mart Tests (`models/marts_postgres/*.yml`)

- Dashboard-ready data validation
- Aggregation accuracy
- Trend calculation verification

### 5. Custom Tests (`tests/*.sql`)

- Cross-model integrity checks
- Complex business rules
- Trend and pattern validation

## Running Tests

### Prerequisites

```bash
# Install dbt packages
dbt deps

# Ensure data is loaded
# Run ingestion assets first
```

### Run All Tests

```bash
dbt test --select tag:github
```

### Run Specific Test Categories

```bash
# Bronze layer only
dbt test --select tag:bronze

# Silver layer only
dbt test --select tag:silver

# Gold layer only
dbt test --select tag:gold

# Marts only
dbt test --select tag:mart
```

### Run Individual Tests

```bash
# Test specific model
dbt test --select stg_github_user_events

# Test specific test
dbt test --select test_github_event_integrity
```

### Run Tests with Data

```bash
# Run models and tests together
dbt build --select tag:github
```

## Test Results Interpretation

### Passing Tests ✅

- Green output indicates all validations passed
- Data meets quality standards for downstream consumption

### Failing Tests ❌

- Red output indicates data quality issues
- Review failure details for remediation steps
- Common failures:
  - `not_null` - Missing required data
  - `accepted_values` - Invalid categorical values
  - `relationships` - Broken foreign key relationships
  - `dbt_expectations` - Statistical or range violations

## Common Test Patterns

### Schema Validation

```yaml
columns:
  - name: event_type
    tests:
      - not_null
      - accepted_values:
          values: ["PushEvent", "IssuesEvent", ...]
```

### Business Rules

```yaml
tests:
  - dbt_expectations.expect_column_values_to_be_between:
      min_value: 0
      max_value: 100
```

### Custom Logic

```sql
{% test test_custom_business_rule(model) %}
    select * from {{ model }}
    where business_rule_violation = true
{% endtest %}
```

## Test Maintenance

### Adding New Tests

1. **Schema tests**: Add to model YAML files
2. **Custom tests**: Create new SQL files in `tests/` directory
3. **Update packages**: Add dependencies to `packages.yml`

### Test Data Requirements

- Tests assume data exists in Iceberg tables
- Run ingestion before testing
- Use `--vars` to parameterize tests for different environments

### CI/CD Integration

```bash
# Run tests in CI pipeline
dbt test --select tag:github --fail-fast

# Generate test reports
dbt docs generate
dbt docs serve
```

## Troubleshooting

### Test Failures

- **Missing data**: Ensure ingestion ran successfully
- **Schema changes**: Update tests when models change
- **Environment issues**: Check connection and permissions

### Performance

- Tests run on sample data for speed
- Use `--threads` to parallelize execution
- Profile slow tests with `dbt --debug test`

### Dependencies

- `dbt_utils`: Utility functions
- `dbt_expectations`: Statistical validations
- `dbt_date`: Date manipulations

## Best Practices

1. **Test early, test often**: Run tests after each model change
2. **Fail fast**: Use `--fail-fast` in CI to catch issues quickly
3. **Document assumptions**: Comment complex business rules
4. **Version tests**: Keep tests in sync with model changes
5. **Monitor coverage**: Ensure critical paths are tested

## Support

For test failures or questions:

1. Check the test output for specific error messages
2. Review model definitions for schema changes
3. Verify data quality in source systems
4. Update tests to match new business requirements
