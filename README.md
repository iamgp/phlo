# Phlo

Modern lakehouse data platform built on Dagster, DLT, Iceberg, and Pandera.

## Features

- **@phlo_ingestion decorator**: Simplified asset creation with automatic schema validation
- **@phlo_quality decorator**: Declarative quality checks (70% less boilerplate)
- **Plugin system**: Extend Phlo with custom connectors and quality checks
- **CLI tools**: `phlo test`, `phlo materialize`, `phlo create-workflow`
- **Testing utilities**: MockIcebergCatalog for fast local testing (<5s)
- **Comprehensive error documentation**: Per-error guides with solutions

## Quick Start

```python
from phlo.ingestion import phlo_ingestion
from phlo.schemas.weather import WeatherObservations

@phlo_ingestion(
    unique_key="observation_id",
    validation_schema=WeatherObservations,
    cron="0 */1 * * *",
)
def weather_observations(partition: str):
    """Fetch weather observations."""
    return fetch_weather_data(partition)
```

## Documentation

- [Testing Guide](docs/TESTING_GUIDE.md)
- [CLI Guide](docs/CLI_GUIDE.md)
- [Phase 3 Features](docs/PHASE_3_FEATURES.md)
- [Error Reference](docs/errors/README.md)

## Installation

```bash
pip install -e .
```

## Development

```bash
# Run tests
phlo test --local

# Create new workflow
phlo create-workflow --domain weather --table observations

# Lint and type check
ruff check .
basedpyright .
```

## License

MIT
