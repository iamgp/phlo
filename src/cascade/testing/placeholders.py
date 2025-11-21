"""
Testing Utilities

Provides testing utilities for Cascade workflows including mock DLT sources,
fixture management, and test helpers.

Status:
- MockDLTSource: ✅ Implemented
- Fixture management: ✅ Implemented
- MockIcebergCatalog: ⚠️  Planned (requires DuckDB integration - 20h effort)
- test_asset_execution: ⚠️  Planned (requires Dagster test harness - 30h effort)

For current testing approaches, see: docs/TESTING_GUIDE.md
"""

import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator, Union, cast
from contextlib import contextmanager


class MockDLTSource:
    """
    Mock DLT source for testing ingestion assets without API calls.

    Creates a DLT-compatible source from test data, allowing you to test
    schema validation, data transformations, and asset logic without
    requiring actual API connections.

    Status: ✅ Fully implemented

    Usage:
        # Direct instantiation
        test_data = [
            {"id": "1", "city": "London", "temp": 15.5},
            {"id": "2", "city": "Paris", "temp": 12.3},
        ]
        source = MockDLTSource(data=test_data, resource_name="weather")

        # Use in asset for testing
        @cascade_ingestion(...)
        def my_asset(partition_date: str):
            if os.getenv("TESTING"):
                return MockDLTSource(data=[...], resource_name="observations")
            else:
                return rest_api({...})  # Real source

        # Or use context manager
        with mock_dlt_source(data=test_data, resource_name="weather") as source:
            # Test your asset logic
            result = process_data(source)
            assert len(result) == 2

    Example with Pandera validation:
        from cascade.schemas.weather import RawWeatherData

        test_data = [{"id": "1", "city": "London", "temp": 15.5}]
        df = pd.DataFrame(test_data)

        # Validate schema works with test data
        validated = RawWeatherData.validate(df)
        assert len(validated) == 1
    """

    def __init__(
        self,
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        resource_name: str = "mock_resource",
    ):
        """
        Initialize mock DLT source.

        Args:
            data: Either list of dictionaries or pandas DataFrame
            resource_name: Name of the mock DLT resource
        """
        if isinstance(data, pd.DataFrame):
            df_data = cast(pd.DataFrame, data)
            self.data = df_data.to_dict('records')
            self._dataframe = df_data
        else:
            self.data = data
            self._dataframe = None

        self.resource_name = resource_name

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over mock data rows."""
        for row in self.data:
            yield row

    def __call__(self):
        """Make the source callable like a DLT resource."""
        return self

    @property
    def name(self) -> str:
        """Return the resource name."""
        return self.resource_name

    def to_pandas(self) -> pd.DataFrame:
        """Convert mock data to pandas DataFrame."""
        if self._dataframe is not None:
            return self._dataframe
        return pd.DataFrame(self.data)

    def __len__(self) -> int:
        """Return number of rows."""
        return len(self.data)

    def __repr__(self) -> str:
        """String representation."""
        return f"MockDLTSource(resource_name='{self.resource_name}', rows={len(self.data)})"


@contextmanager
def mock_dlt_source(
    data: Union[List[Dict[str, Any]], pd.DataFrame],
    resource_name: str = "mock_resource",
):
    """
    Context manager for mocking DLT sources.

    Status: ✅ Fully implemented

    Args:
        data: Either list of dictionaries or pandas DataFrame
        resource_name: Name of the mock DLT resource

    Yields:
        MockDLTSource instance

    Example:
        def test_my_asset():
            test_data = [
                {"id": "1", "value": 42},
                {"id": "2", "value": 84},
            ]

            with mock_dlt_source(data=test_data, resource_name="test") as source:
                # Test your asset logic
                result = my_asset_function(source)
                assert result is not None
                assert len(source) == 2

        def test_with_dataframe():
            test_df = pd.DataFrame([
                {"id": "1", "value": 42},
            ])

            with mock_dlt_source(data=test_df, resource_name="test") as source:
                # Validate schema
                validated = MySchema.validate(source.to_pandas())
                assert len(validated) == 1
    """
    source = MockDLTSource(data, resource_name)
    try:
        yield source
    finally:
        pass


class MockIcebergCatalog:
    """
    Mock Iceberg catalog for testing without Docker.

    Status: ⚠️ Planned implementation (requires DuckDB integration)

    This would require:
    - DuckDB as in-memory backend
    - PyIceberg table operations mapped to DuckDB
    - Schema translation
    - Approximately 20 hours of development

    For now, use full Docker stack for integration testing.
    See: docs/TESTING_GUIDE.md#integration-testing

    Usage (planned API):
        with mock_iceberg_catalog() as catalog:
            table = catalog.create_table("test.table", schema=...)
            table.append(data)
            result = table.scan().to_arrow()
    """

    def __init__(self):
        """Initialize mock Iceberg catalog."""
        self.tables: Dict[str, Any] = {}

    def create_table(self, name: str, schema: Any) -> Any:
        """Create a mock table (not yet implemented)."""
        raise NotImplementedError(
            "MockIcebergCatalog is planned but not yet implemented. "
            "Implementation requires DuckDB integration (~20 hours). "
            "\n\n"
            "For now, use full Docker stack for integration testing:\n"
            "1. Start Docker: make up-core up-query\n"
            "2. Run integration tests: pytest tests/ -m integration\n"
            "\n"
            "See docs/TESTING_GUIDE.md#integration-testing"
        )


@contextmanager
def mock_iceberg_catalog():
    """
    Context manager for mocking Iceberg catalog.

    Status: ⚠️ Planned implementation

    See MockIcebergCatalog class for details on planned implementation.
    """
    catalog = MockIcebergCatalog()
    try:
        yield catalog
    finally:
        pass


def test_asset_execution(
    asset: Any,
    partition: str,
    mock_data: Optional[List[Dict[str, Any]]] = None,
    mock_catalog: bool = True,
) -> Any:
    """
    Test asset execution without full Docker stack.

    Status: ⚠️ Planned implementation (requires Dagster test harness)

    This would require:
    - Dagster context mocking
    - Resource dependency injection
    - MaterializeResult validation
    - Approximately 30 hours of development

    For now, use Dagster's built-in testing tools:

    Example (current approach):
        from dagster import materialize

        def test_my_asset():
            # Requires Docker services running
            result = materialize([my_asset])
            assert result.success

    See: docs/TESTING_GUIDE.md#integration-testing
    """
    raise NotImplementedError(
        "test_asset_execution is planned but not yet implemented. "
        "Implementation requires Dagster test harness integration (~30 hours). "
        "\n\n"
        "For now, use Dagster's materialize() or Docker exec:\n"
        "1. Dagster materialize: from dagster import materialize\n"
        "2. Docker exec: docker exec dagster-webserver dagster asset materialize ...\n"
        "3. Dagster UI: http://localhost:3000\n"
        "\n"
        "See docs/TESTING_GUIDE.md for examples"
    )


# Fixture Management - ✅ Implemented


def load_fixture(path: Union[str, Path]) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load test fixture from file.

    Status: ✅ Fully implemented

    Supports JSON, CSV, and Parquet files. Automatically detects format
    from file extension.

    Args:
        path: Path to fixture file (.json, .csv, or .parquet)

    Returns:
        Loaded data as DataFrame, dict, or list of dicts depending on format

    Example:
        # Load JSON fixture
        test_data = load_fixture("tests/fixtures/weather_data.json")

        # Use in test
        with mock_dlt_source(data=test_data) as source:
            result = my_asset_function(source)

        # Load CSV fixture
        test_df = load_fixture("tests/fixtures/sample_data.csv")
        validated = MySchema.validate(test_df)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, 'r') as f:
            data = json.load(f)
        # If it's a list of dicts, return as-is for easy use with MockDLTSource
        # If it's a dict, return as-is
        return data

    elif suffix == ".csv":
        return pd.read_csv(path)

    elif suffix == ".parquet":
        return pd.read_parquet(path)

    else:
        raise ValueError(
            f"Unsupported fixture format: {suffix}. "
            "Supported formats: .json, .csv, .parquet"
        )


def save_fixture(
    data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
    path: Union[str, Path],
    pretty: bool = True,
) -> None:
    """
    Save test data as fixture file.

    Status: ✅ Fully implemented

    Automatically determines format from file extension.
    Creates parent directories if they don't exist.

    Args:
        data: Data to save (DataFrame, dict, or list of dicts)
        path: Path to save fixture file (.json, .csv, or .parquet)
        pretty: If True, format JSON with indentation (default: True)

    Example:
        # Save test data for reuse
        test_data = [
            {"id": "1", "value": 42},
            {"id": "2", "value": 84},
        ]
        save_fixture(test_data, "tests/fixtures/sample_data.json")

        # Save DataFrame
        df = pd.DataFrame(test_data)
        save_fixture(df, "tests/fixtures/sample_data.csv")

        # Later, load it in tests
        loaded = load_fixture("tests/fixtures/sample_data.json")

    Raises:
        ValueError: If file format is not supported
    """
    path = Path(path)

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2, default=str)
            else:
                json.dump(data, f, default=str)

    elif suffix == ".csv":
        if isinstance(data, pd.DataFrame):
            df_data = cast(pd.DataFrame, data)
            df_data.to_csv(path, index=False)
        else:
            # Convert to DataFrame first
            df: pd.DataFrame = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            df.to_csv(path, index=False)

    elif suffix == ".parquet":
        if isinstance(data, pd.DataFrame):
            df_data = cast(pd.DataFrame, data)
            df_data.to_parquet(path, index=False)
        else:
            # Convert to DataFrame first
            df: pd.DataFrame = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
            df.to_parquet(path, index=False)

    else:
        raise ValueError(
            f"Unsupported fixture format: {suffix}. "
            "Supported formats: .json, .csv, .parquet"
        )


# Implementation Roadmap
# =====================
#
# ✅ Phase 1 (Complete): MockDLTSource and fixture management
# ⚠️  Phase 2 (Planned - 20h): Mock Iceberg catalog using DuckDB
# ⚠️  Phase 3 (Planned - 30h): Test asset execution framework
# ⚠️  Phase 4 (Planned - 10h): Test coverage reporting
#
# Total estimated: ~60 hours remaining
#
# Priority: HIGH (significantly improves developer experience)
#
# See: docs/audit/testing_experience_audit.md for full requirements
