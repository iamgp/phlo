# Phlo CLI Guide

Command-line interface for Phlo workflows.

## Installation

The Phlo CLI is automatically available after installing Phlo:

```bash
# Install Phlo
pip install -e .

# Verify installation
phlo --version
```

---

## Commands Overview

| Command | Description | Speed |
|---------|-------------|-------|
| `phlo test` | Run tests with optional local mode | Fast (< 5s local) |
| `phlo materialize` | Materialize assets via Docker | Medium (30-60s) |
| `phlo create-workflow` | Interactive workflow scaffolding | Fast (< 10s) |

---

## phlo test

Run tests for Phlo workflows.

### Usage

```bash
phlo test [ASSET_NAME] [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `ASSET_NAME` | (Optional) Run tests for specific asset |
| `--local` | Run tests locally without Docker |
| `--coverage` | Generate coverage report |
| `-v, --verbose` | Verbose output |
| `-m, --marker MARKER` | Run tests with specific pytest marker |

### Examples

**Run all tests**:
```bash
phlo test
```

**Run tests for specific asset**:
```bash
phlo test weather_observations
```

**Run unit tests only (skip Docker integration tests)**:
```bash
phlo test --local
```

**Generate coverage report**:
```bash
phlo test --coverage
# Opens htmlcov/index.html
```

**Run integration tests only**:
```bash
phlo test -m integration
```

**Verbose output**:
```bash
phlo test -v
```

### Performance

| Mode | Docker Required | Speed | Best For |
|------|----------------|-------|----------|
| `phlo test --local` | ❌ No | < 5s | Unit tests, CI/CD |
| `phlo test` | ✅ Yes | 30-60s | Integration tests |

### Test Markers

Mark your tests with pytest markers:

```python
import pytest

# Unit test (runs with --local)
def test_schema():
    pass

# Integration test (skipped with --local)
@pytest.mark.integration
def test_full_pipeline():
    pass
```

---

## phlo materialize

Materialize Dagster assets via Docker.

### Usage

```bash
phlo materialize ASSET_NAME [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `ASSET_NAME` | Asset to materialize |
| `-p, --partition DATE` | Partition date (YYYY-MM-DD) |
| `--select SELECTOR` | Asset selector expression |
| `--dry-run` | Show command without executing |

### Examples

**Materialize asset**:
```bash
phlo materialize weather_observations
```

**Materialize with partition**:
```bash
phlo materialize weather_observations --partition 2024-01-15
```

**Use Dagster selector**:
```bash
phlo materialize --select "tag:weather"
phlo materialize --select "*weather*"
```

**Dry run (show command without executing)**:
```bash
phlo materialize weather_observations --dry-run
# Output: docker exec dagster-webserver dagster asset materialize --select weather_observations
```

### Requirements

- Docker services must be running
- `dagster-webserver` container must be up

```bash
# Start services
make up-core up-query

# Verify services
docker ps | grep dagster-webserver
```

### Behind the Scenes

`phlo materialize` is a convenience wrapper for:

```bash
docker exec dagster-webserver dagster asset materialize --select <asset>
```

---

## phlo create-workflow

Interactive workflow scaffolding.

### Usage

```bash
phlo create-workflow [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Workflow type (ingestion, transform, quality) | Prompt |
| `--domain DOMAIN` | Domain name (e.g., weather, stripe) | Prompt |
| `--table TABLE` | Table name | Prompt |
| `--unique-key KEY` | Unique key field for deduplication | Prompt |
| `--cron CRON` | Cron schedule expression | `"0 */1 * * *"` |
| `--api-base-url URL` | REST API base URL | Prompt |

### Examples

**Interactive mode** (recommended for first-time users):
```bash
phlo create-workflow

# Prompts:
# Workflow type: ingestion
# Domain name: weather
# Table name: observations
# Unique key field: id
# Cron schedule: 0 */1 * * *
# API base URL: https://api.openweathermap.org/data/3.0
```

**Command-line mode** (for automation):
```bash
phlo create-workflow \
  --type ingestion \
  --domain weather \
  --table observations \
  --unique-key id \
  --cron "0 */1 * * *" \
  --api-base-url "https://api.example.com/v1"
```

### What It Creates

The command generates 3 files:

1. **Pandera schema** (`src/phlo/schemas/{domain}.py`)
2. **Ingestion asset** (`src/phlo/defs/ingestion/{domain}/{table}.py`)
3. **Test file** (`tests/test_{domain}_{table}.py`)

And auto-registers the domain in `src/phlo/defs/ingestion/__init__.py`.

### Example Output

```bash
🚀 Creating ingestion workflow for weather.observations...

✅ Created files:

  ✓ src/phlo/schemas/weather.py
  ✓ src/phlo/defs/ingestion/weather/observations.py
  ✓ tests/test_weather_observations.py

📝 Next steps:
  1. Edit schema: src/phlo/schemas/weather.py
  2. Configure API: src/phlo/defs/ingestion/weather/observations.py
  3. Restart Dagster: docker restart dagster-webserver
  4. Test: phlo test weather
  5. Materialize: phlo materialize observations
```

### File Templates

Generated files include:
- ✅ Complete TODOs for customization
- ✅ Inline documentation
- ✅ Best practices examples
- ✅ Common API patterns (authentication, pagination, etc.)

### After Creation

1. **Edit schema** - Add your fields to the Pandera schema
2. **Configure API** - Update the DLT rest_api configuration
3. **Restart Dagster** - `docker restart dagster-webserver`
4. **Test locally** - `phlo test {domain} --local`
5. **Materialize** - `phlo materialize {table}`

---

## Global Options

All commands support:

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Examples

```bash
# Show help
phlo --help
phlo test --help
phlo materialize --help
phlo create-workflow --help

# Show version
phlo --version
```

---

## Comparison with Manual Approach

| Task | Manual | With CLI | Time Saved |
|------|--------|----------|------------|
| **Create workflow** | 15-20 min | 5-10 min | 50-67% |
| **Run tests** | `pytest tests/` | `phlo test` | Slight |
| **Materialize asset** | `docker exec dagster-webserver dagster asset materialize ...` | `phlo materialize {asset}` | 70% fewer keystrokes |
| **Local testing** | Manual pytest markers | `phlo test --local` | Easier |

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          phlo test --local --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - phlo test --local --coverage
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## Troubleshooting

### "phlo: command not found"

**Solution**:
```bash
# Install in editable mode
pip install -e .

# Or ensure PATH includes Python scripts directory
export PATH="$HOME/.local/bin:$PATH"
```

### "Docker not found or dagster-webserver container not running"

**Solution**:
```bash
# Start Docker services
make up-core up-query

# Verify
docker ps | grep dagster-webserver
```

### "Test file not found"

**Solution**:
```bash
# List available test files
ls tests/test_*.py

# Use exact asset name
phlo test weather_observations  # Looks for tests/test_weather_observations.py
```

### "Files already exist" (create-workflow)

**Solution**:
```bash
# Check existing files
ls src/phlo/schemas/
ls src/phlo/defs/ingestion/

# Delete old files if you want to regenerate
rm src/phlo/schemas/weather.py
rm -r src/phlo/defs/ingestion/weather/
rm tests/test_weather_observations.py
```

---

## Best Practices

### 1. Use `--local` for Fast Iteration

```bash
# Fast feedback loop
phlo test --local

# Only run full integration tests when needed
phlo test -m integration
```

### 2. Use `--dry-run` Before Production Materializations

```bash
# Check command first
phlo materialize critical_asset --dry-run

# Then execute
phlo materialize critical_asset
```

### 3. Create Workflows with CLI

```bash
# Consistent structure
phlo create-workflow

# vs manual (error-prone)
# 1. Create schema file
# 2. Create asset file
# 3. Create test file
# 4. Register domain
# 5. Fix import errors
```

### 4. Add Coverage Checks to CI

```yaml
- name: Run tests with coverage
  run: phlo test --coverage

- name: Check coverage threshold
  run: |
    coverage report --fail-under=80
```

---

## Advanced Usage

### Custom Test Organization

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )

# Run fast tests only
# phlo test -m "not slow and not integration"
```

### Selective Asset Materialization

```bash
# Materialize all assets in a group
phlo materialize --select "group:weather"

# Materialize all dependencies
phlo materialize --select "weather_observations+"

# Materialize all dependents
phlo materialize --select "+weather_observations"
```

---

## Next Steps

- **Create your first workflow**: `phlo create-workflow`
- **Test it locally**: `phlo test {domain} --local`
- **Materialize data**: `phlo materialize {table}`
- **Read testing guide**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)

---

## Feedback

Found a bug or have a feature request?
- **GitHub Issues**: https://github.com/iamgp/phlo/issues
- **GitHub Discussions**: https://github.com/iamgp/phlo/discussions
