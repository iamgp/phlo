# Contributing to Cascade

Thank you for your interest in contributing to Cascade! This guide will help you understand the project structure, development workflow, and best practices.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Code Style and Standards](#code-style-and-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Submitting Changes](#submitting-changes)

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- `uv` for Python package management

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/phlo.git
cd phlo

# Install dependencies
make setup

# Start services
make up-core up-query

# Run tests
make test
```

## Project Structure

Cascade follows the **src-layout** pattern with clear separation between framework code and user-defined workflows.

### Directory Organization

```
phlo/
├── src/phlo/              # Framework source code
│   ├── ingestion/            # Ingestion framework (decorator, helpers)
│   ├── schemas/              # Schema definitions and converter
│   ├── iceberg/              # Iceberg catalog and table management
│   ├── defs/                 # User-defined workflows
│   │   ├── ingestion/        # Data ingestion assets
│   │   │   ├── domain/       # Domain-specific ingestion (github, nightscout, etc.)
│   │   ├── transform/        # dbt transformations
│   │   ├── publishing/       # Publishing to Postgres
│   │   ├── quality/          # Data quality checks
│   │   ├── validation/       # Validation assets
│   │   ├── nessie/           # Nessie branch management
│   │   ├── sensors/          # Dagster sensors
│   │   ├── schedules/        # Dagster schedules
│   │   ├── resources/        # Dagster resources
│   │   └── jobs/             # Job definitions
│   ├── definitions.py        # Main Dagster definitions
│   └── config.py             # Pydantic settings configuration
├── tests/                    # Test suite
├── docs/                     # Documentation
└── dbt_project/              # dbt transformations
```

### Folder Structure Guidelines

Based on the [Folder Structure Audit](docs/audit/folder_structure_analysis.md):

**Depth Guideline**: Keep file paths ≤ 4 levels deep
- ✅ Good: `src/phlo/defs/transform/dbt.py` (4 levels)
- ⚠️ Acceptable: `src/phlo/defs/ingestion/domain/asset.py` (5 levels)
- ❌ Avoid: Deeper nesting

**Naming Conventions**:
- Lowercase with underscores: `glucose_entries.py`
- Descriptive names: `nightscout/glucose.py` (not `ns/gluc.py`)
- Capabilities are singular: `ingestion/`, `transform/` (not `ingestions/`)
- Domains use their actual names: `github/`, `nightscout/`

### Where to Add New Code

**New Ingestion Asset**:
1. Create schema: `src/phlo/schemas/domain.py`
2. Create asset: `src/phlo/defs/ingestion/domain/asset_name.py`
3. Register domain: Add import in `src/phlo/defs/ingestion/__init__.py`

**New Transformation**:
1. Add dbt model: `dbt_project/models/layer/model_name.sql`
2. Follow dbt naming conventions: `stg_*` (bronze), `fct_*` (silver), `mrt_*` (marts)

**New Quality Check**:
1. Create asset: `src/phlo/defs/quality/domain.py`
2. Use Dagster asset decorator with quality checks

**New Publishing Configuration**:
1. Edit: `src/phlo/defs/publishing/config.yaml`
2. Add table mappings and dependencies

**New Job Configuration**:
1. Edit: `src/phlo/defs/jobs/config.yaml`
2. Define asset selection and partitions

## Development Workflow

### Creating a New Ingestion Workflow

Based on the [Workflow Creation Audit](docs/audit/workflow_creation_audit.md):

**Time Estimate**: 15-20 minutes

**Step 1: Define Schema** (3-5 min)
```python
# src/phlo/schemas/weather.py
import pandera as pa
from pandera.typing import Series

class RawWeatherObservations(pa.DataFrameModel):
    """Schema for raw weather observations."""
    city_name: Series[str] = pa.Field(description="City name")
    temperature: Series[float] = pa.Field(ge=-100, le=100)
    humidity: Series[int] = pa.Field(ge=0, le=100)
    timestamp: Series[str] = pa.Field(description="ISO 8601 timestamp")

    class Config:
        strict = True
        coerce = True
```

**Step 2: Create Ingestion Asset** (5-7 min)
```python
# src/phlo/defs/ingestion/weather/observations.py
from dlt.sources.rest_api import rest_api
from phlo.ingestion import cascade_ingestion
from phlo.schemas.weather import RawWeatherObservations

@cascade_ingestion(
    table_name="weather_observations",
    unique_key="id",
    validation_schema=RawWeatherObservations,
    group="weather",
    cron="0 */1 * * *",
    freshness_hours=(1, 24),
)
def weather_observations(partition_date: str):
    """Ingest weather observations using DLT rest_api source."""
    start_time = f"{partition_date}T00:00:00.000Z"
    end_time = f"{partition_date}T23:59:59.999Z"

    source = rest_api({
        "client": {
            "base_url": "https://api.openweathermap.org/data/3.0",
            "auth": {"token": "API_KEY"}
        },
        "resources": [{
            "name": "observations",
            "endpoint": {
                "path": "onecall/timemachine",
                "params": {"dt": partition_date}
            }
        }]
    })

    return source
```

**Step 3: Register Domain** (1 min)
```python
# src/phlo/defs/ingestion/__init__.py
from phlo.defs.ingestion import github  # noqa: F401
from phlo.defs.ingestion import nightscout  # noqa: F401
from phlo.defs.ingestion import weather  # noqa: F401  # <- ADD THIS
```

**Step 4: Test**
```bash
# Restart Dagster
docker restart dagster-webserver

# Materialize asset
docker exec dagster-webserver dagster asset materialize \
  --select weather_observations \
  --partition 2024-01-15
```

### Built-in Functionality

Based on the [Functionality Inventory](docs/audit/functionality_inventory.md):

**Use the `@cascade_ingestion` decorator** - It provides:
- 74% boilerplate reduction (270 lines → 60 lines)
- Automatic DLT pipeline setup
- Pandera schema validation
- PyIceberg schema auto-generation
- Idempotent deduplication
- Timing instrumentation
- Error handling and retries

**Leverage YAML configuration** for:
- Job definitions (`defs/jobs/config.yaml`)
- Publishing configuration (`defs/publishing/config.yaml`)

**Use dbt for transformations** - Don't write Python for SQL logic:
- Bronze layer: `stg_*` models
- Silver layer: `fct_*` and `dim_*` models
- Marts layer: `mrt_*` models

## Code Style and Standards

### Python Code Standards

**Tools**:
- Package manager: `uv`
- Linter/formatter: `ruff`
- Type checker: `basedpyright`
- Line length: 100 characters

**Commands**:
```bash
# Format code
ruff format phlo/

# Lint code
ruff check phlo/

# Type check
basedpyright phlo/
```

### Code Quality Guidelines

**From Framework Design**:
1. Prefer declarative over imperative (use decorators and YAML)
2. Single Responsibility Principle (each asset does one thing)
3. DRY (Don't Repeat Yourself) - use helpers and decorators
4. Type hints everywhere (enables auto-completion and type checking)
5. Comprehensive docstrings (see existing code for examples)

**Schema Definitions**:
- Always use Pandera DataFrameModel
- Include field descriptions (`pa.Field(description="...")`)
- Add constraints where appropriate (`ge=0`, `le=100`)
- Use `strict = True` in Config for validation

**Ingestion Assets**:
- Keep fetch functions simple (just return DLT source)
- Let decorator handle all boilerplate
- Use descriptive names (`github_user_events`, not `fetch_data`)
- Document partition_date parameter usage

## Testing

Based on the [Testing Experience Audit](docs/audit/testing_experience_audit.md):

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_ingestion_decorator.py

# Run with coverage
pytest --cov=phlo tests/
```

### Test Structure

```
tests/
├── test_ingestion_decorator.py    # Decorator tests
├── test_schema_converter.py       # Schema auto-generation tests
├── test_iceberg.py                # Iceberg integration tests
├── test_resources.py              # Resource tests
└── test_system_e2e.py             # End-to-end tests
```

### Writing Tests

**Unit Tests** (for framework code):
```python
import pytest
from phlo.ingestion import cascade_ingestion

def test_decorator_basic_functionality():
    """Test cascade_ingestion decorator creates valid asset."""
    @cascade_ingestion(
        table_name="test_table",
        unique_key="id",
        group="test",
    )
    def test_asset(partition_date: str):
        return []

    assert test_asset is not None
    # Add more assertions
```

**Integration Tests** (require Docker):
```bash
# Start test environment
make up-core up-query

# Run integration tests
pytest tests/test_system_e2e.py
```

### Testing Gaps (Future Improvements)

Based on audit findings, we plan to add:
- Testing utilities module (`phlo.testing`)
- Mock DLT sources for unit tests
- Local test mode (no Docker required)
- Comprehensive testing guide

## Documentation

Based on the [Documentation Gap Analysis](docs/audit/documentation_gap_analysis.md):

### Documentation Standards

**Required for all new features**:
1. Docstrings in code (Google style)
2. Update relevant guide (WORKFLOW_DEVELOPMENT_GUIDE.md, etc.)
3. Add example if introducing new pattern
4. Update TROUBLESHOOTING_GUIDE.md if introducing new error scenarios

**Documentation Files**:
- **QUICKSTART.md**: 10-minute getting started (for first-time users)
- **WORKFLOW_DEVELOPMENT_GUIDE.md**: Complete tutorial (for building pipelines)
- **BEGINNERS_GUIDE.md**: Concepts and architecture (for understanding)
- **BEST_PRACTICES_GUIDE.md**: Production patterns (for experienced users)
- **TROUBLESHOOTING_GUIDE.md**: Common errors and solutions

### Writing Documentation

**Style Guidelines**:
- Clear, concise language
- Step-by-step instructions with commands
- Real-world examples (not toy examples)
- Include expected output
- Add "Why" context (not just "How")

**Code Examples**:
- Must be copy-paste ready
- Include imports
- Include error handling where relevant
- Test all examples before committing

## Submitting Changes

### Pull Request Process

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**
- Follow code style guidelines
- Write tests for new functionality
- Update documentation

3. **Run Quality Checks**
```bash
# Format
ruff format phlo/

# Lint
ruff check phlo/

# Type check
basedpyright phlo/

# Test
pytest tests/
```

4. **Commit Changes**
```bash
git add .
git commit -m "feat: add weather ingestion support

- Add weather schema with Pandera validation
- Create weather observations ingestion asset
- Update documentation with weather example
- Add integration tests

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

5. **Push and Create PR**
```bash
git push -u origin feature/your-feature-name

# Create PR via GitHub UI or gh CLI
gh pr create --title "feat: add weather ingestion support" \
  --body "## Summary
- Add weather data ingestion
- Includes schema validation
- Full test coverage

## Testing
- Tested with OpenWeather API
- All tests passing

## Documentation
- Updated WORKFLOW_DEVELOPMENT_GUIDE.md
- Added weather example"
```

### Commit Message Guidelines

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(ingestion): add weather data source support

fix(schema): handle null values in temperature field

docs: update QUICKSTART with weather example

refactor(decorator): simplify error handling logic
```

### Code Review Process

**What Reviewers Look For**:
1. Code follows style guidelines
2. Tests cover new functionality
3. Documentation is updated
4. No breaking changes (or clearly documented)
5. Error messages are helpful
6. Performance considerations addressed

**Responding to Feedback**:
- Address all comments
- Ask questions if unclear
- Update PR description if scope changes
- Re-request review after changes

## Common Patterns and Anti-Patterns

### Do's ✅

**Ingestion**:
- Use `@cascade_ingestion` decorator
- Define schemas with Pandera
- Return DLT sources from fetch functions
- Document API authentication requirements

**Transformations**:
- Use dbt for SQL transformations
- Follow bronze/silver/gold layer pattern
- Use `ref()` for dependencies
- Test transformations with dbt test

**Quality**:
- Add Pandera constraints to schemas
- Create Dagster asset checks
- Log quality metrics
- Fail loud on critical issues

### Don'ts ❌

**Ingestion**:
- Don't write manual DLT setup code (use decorator)
- Don't duplicate schemas (use schema auto-generation)
- Don't write raw Iceberg operations (decorator handles it)
- Don't forget to register domain imports

**Transformations**:
- Don't write SQL in Python (use dbt)
- Don't create circular dependencies
- Don't hardcode table names (use `ref()`)

**General**:
- Don't commit sensitive data (API keys, passwords)
- Don't skip tests
- Don't merge without review
- Don't use broad exception catching

## Resources

### Audit Documents

Comprehensive usability audit (Issue #21):
- [Executive Summary](docs/audit/executive_summary.md)
- [Folder Structure Analysis](docs/audit/folder_structure_analysis.md)
- [Workflow Creation Audit](docs/audit/workflow_creation_audit.md)
- [Functionality Inventory](docs/audit/functionality_inventory.md)
- [Testing Experience Audit](docs/audit/testing_experience_audit.md)
- [Documentation Gap Analysis](docs/audit/documentation_gap_analysis.md)
- [Error Message Audit](docs/audit/error_message_audit.md)

### External Documentation

- **Apache Iceberg**: https://iceberg.apache.org/docs/latest/
- **Project Nessie**: https://projectnessie.org/
- **Dagster**: https://docs.dagster.io/
- **dbt**: https://docs.getdbt.com/
- **DLT**: https://dlthub.com/docs/
- **Pandera**: https://pandera.readthedocs.io/

## Questions?

- Open a GitHub Issue for bugs or feature requests
- Start a GitHub Discussion for questions
- Check existing documentation in `docs/`

**Thank you for contributing to Cascade!**
