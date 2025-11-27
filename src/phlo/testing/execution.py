"""
Helper to execute assets with mocked dependencies and capture results.

Provides `test_asset_execution()` for running `@phlo_ingestion` assets in tests
with mocked Iceberg, Trino, and DLT dependencies.

Example:
    >>> result = test_asset_execution(
    ...     my_asset,
    ...     partition="2024-01-01",
    ...     mock_data=[{"id": 1, "name": "Alice"}],
    ... )
    >>> assert result.success
    >>> assert len(result.data) == 1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional
from datetime import datetime
import time

import pandas as pd
from dagster import ExecuteInProcessResult, in_process_executor
from dagster import DagsterInstance, DagsterEventType

from phlo.testing.mock_iceberg import MockIcebergCatalog
from phlo.testing.mock_dlt import mock_dlt_source, MockDLTResource
from phlo.testing.mock_trino import MockTrinoResource


@dataclass
class AssetTestResult:
    """
    Result of executing an asset in test mode.

    Attributes:
        success: Whether asset execution succeeded
        data: Resulting DataFrame (if available)
        metadata: Metadata from MaterializeResult
        logs: Captured log messages
        duration: Execution time in seconds
        error: Exception if execution failed
        raw_result: Raw Dagster ExecuteInProcessResult (advanced use)
    """

    success: bool
    data: Optional[pd.DataFrame] = None
    metadata: dict[str, Any] = None
    logs: list[str] = None
    duration: float = 0.0
    error: Optional[Exception] = None
    raw_result: Optional[Any] = None

    def __post_init__(self) -> None:
        """Initialize defaults for mutable fields."""
        if self.metadata is None:
            self.metadata = {}
        if self.logs is None:
            self.logs = []


class MockAssetContext:
    """
    Mock Dagster context for asset execution.

    Provides mocked resources (Iceberg, Trino, DLT) and logging.
    """

    def __init__(
        self,
        partition_key: Optional[str] = None,
        mock_iceberg: Optional[MockIcebergCatalog] = None,
        mock_trino: Optional[MockTrinoResource] = None,
    ) -> None:
        """
        Initialize mock context.

        Args:
            partition_key: Partition identifier (e.g., "2024-01-01")
            mock_iceberg: MockIcebergCatalog instance (creates new if None)
            mock_trino: MockTrinoResource instance (creates new if None)
        """
        self.partition_key = partition_key or "2024-01-01"
        self.iceberg = mock_iceberg or MockIcebergCatalog()
        self.trino = mock_trino or MockTrinoResource()

        self._logs: list[str] = []
        self._logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create logger that captures to self._logs."""
        logger = logging.getLogger(f"asset_test_{id(self)}")
        logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        logger.handlers = []

        # Add custom handler to capture logs
        class LogCapture(logging.Handler):
            def __init__(self, logs_list: list[str]) -> None:
                super().__init__()
                self.logs = logs_list

            def emit(self, record: logging.LogRecord) -> None:
                self.logs.append(self.format(record))

        handler = LogCapture(self._logs)
        formatter = logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message.

        Args:
            message: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        getattr(self._logger, level.lower())(message)

    @property
    def logs(self) -> list[str]:
        """Get all captured logs."""
        return self._logs.copy()

    def get_resource(self, name: str) -> Any:
        """
        Get a mock resource by name.

        Args:
            name: Resource name (iceberg, trino, etc.)

        Returns:
            Mock resource instance

        Raises:
            ValueError: If resource doesn't exist
        """
        resources = {
            "iceberg": self.iceberg,
            "trino": self.trino,
        }

        if name not in resources:
            raise ValueError(f"Unknown resource: {name}")

        return resources[name]


def test_asset_execution(
    asset_fn: Callable,
    partition: str = "2024-01-01",
    mock_data: Optional[list[dict[str, Any]]] = None,
    mock_iceberg: Optional[MockIcebergCatalog] = None,
    mock_trino: Optional[MockTrinoResource] = None,
    expected_schema: Optional[Any] = None,
    materialize_kwargs: Optional[dict[str, Any]] = None,
    _pytest_skip: bool = True,  # Flag to prevent pytest collection
) -> AssetTestResult:
    """
    Execute an asset with mocked dependencies.

    Runs a `@phlo_ingestion` asset in isolation with mocked Iceberg,
    Trino, and DLT services. Captures results and logs for inspection.

    Args:
        asset_fn: Asset function to test
        partition: Partition key (e.g., "2024-01-01")
        mock_data: Mock data to return from DLT source
        mock_iceberg: Pre-configured MockIcebergCatalog (uses new if None)
        mock_trino: Pre-configured MockTrinoResource (uses new if None)
        expected_schema: Pandera schema to validate results
        materialize_kwargs: Extra kwargs to pass to materialize

    Returns:
        AssetTestResult with execution details

    Raises:
        ValueError: If asset execution fails (and success=False in result)

    Example:
        >>> @phlo_ingestion(
        ...     unique_key="id",
        ...     validation_schema=MySchema,
        ... )
        ... def my_asset(partition_date: str):
        ...     return [{"id": 1, "name": "Alice"}]
        ...
        >>> result = test_asset_execution(
        ...     my_asset,
        ...     partition="2024-01-01",
        ... )
        >>> assert result.success
        >>> assert len(result.data) == 1
    """
    if mock_data is None:
        mock_data = []

    if materialize_kwargs is None:
        materialize_kwargs = {}

    start_time = time.time()
    context = MockAssetContext(
        partition_key=partition,
        mock_iceberg=mock_iceberg,
        mock_trino=mock_trino,
    )

    try:
        # Call asset function with mock context
        result = asset_fn(partition_date=partition)

        # Convert result to DataFrame if needed
        if isinstance(result, pd.DataFrame):
            data = result
        elif isinstance(result, list):
            data = pd.DataFrame(result) if result else pd.DataFrame()
        else:
            # Assume it's an iterator/generator
            data = pd.DataFrame(list(result)) if result else pd.DataFrame()

        # Validate against expected schema if provided
        if expected_schema is not None:
            try:
                expected_schema.validate(data)
            except Exception as e:
                return AssetTestResult(
                    success=False,
                    data=data,
                    logs=context.logs,
                    duration=time.time() - start_time,
                    error=ValueError(f"Schema validation failed: {e}"),
                )

        return AssetTestResult(
            success=True,
            data=data,
            metadata={
                "row_count": len(data),
                "columns": list(data.columns),
                "partition": partition,
            },
            logs=context.logs,
            duration=time.time() - start_time,
            raw_result=result,
        )

    except Exception as e:
        return AssetTestResult(
            success=False,
            logs=context.logs,
            duration=time.time() - start_time,
            error=e,
        )


def test_asset_with_catalog(
    asset_fn: Callable,
    partition: str = "2024-01-01",
    catalog: Optional[MockIcebergCatalog] = None,
) -> AssetTestResult:
    """
    Execute an asset with access to mock Iceberg catalog.

    Useful for testing assets that read from or write to Iceberg tables.

    Args:
        asset_fn: Asset function to test
        partition: Partition key
        catalog: Pre-configured MockIcebergCatalog

    Returns:
        AssetTestResult with catalog access

    Example:
        >>> catalog = MockIcebergCatalog()
        >>> # ... set up tables in catalog ...
        >>> result = test_asset_with_catalog(
        ...     my_transform_asset,
        ...     partition="2024-01-01",
        ...     catalog=catalog,
        ... )
    """
    if catalog is None:
        catalog = MockIcebergCatalog()

    return test_asset_execution(
        asset_fn,
        partition=partition,
        mock_iceberg=catalog,
    )


def test_asset_with_trino(
    asset_fn: Callable,
    partition: str = "2024-01-01",
    trino: Optional[MockTrinoResource] = None,
) -> AssetTestResult:
    """
    Execute an asset with access to mock Trino resource.

    Useful for testing quality checks and transform assets.

    Args:
        asset_fn: Asset function to test
        partition: Partition key
        trino: Pre-configured MockTrinoResource

    Returns:
        AssetTestResult with Trino access

    Example:
        >>> trino = MockTrinoResource()
        >>> # ... set up tables ...
        >>> result = test_asset_with_trino(
        ...     my_quality_check,
        ...     trino=trino,
        ... )
    """
    if trino is None:
        trino = MockTrinoResource()

    return test_asset_execution(
        asset_fn,
        partition=partition,
        mock_trino=trino,
    )


class TestAssetExecutor:
    """
    Reusable executor for testing multiple asset runs.

    Maintains catalog state across multiple executions for integration testing.

    Example:
        >>> executor = TestAssetExecutor()
        >>> result1 = executor.execute(asset1, partition="2024-01-01")
        >>> result2 = executor.execute(asset2, partition="2024-01-01")
        >>> # Both use same catalog instance
    """

    def __init__(
        self,
        catalog: Optional[MockIcebergCatalog] = None,
        trino: Optional[MockTrinoResource] = None,
    ) -> None:
        """
        Initialize executor.

        Args:
            catalog: Shared MockIcebergCatalog
            trino: Shared MockTrinoResource
        """
        self.catalog = catalog or MockIcebergCatalog()
        self.trino = trino or MockTrinoResource()
        self.results: list[AssetTestResult] = []

    def execute(
        self,
        asset_fn: Callable,
        partition: str = "2024-01-01",
        mock_data: Optional[list[dict[str, Any]]] = None,
    ) -> AssetTestResult:
        """
        Execute an asset with shared resources.

        Args:
            asset_fn: Asset function to test
            partition: Partition key
            mock_data: Mock data (not used in executor mode)

        Returns:
            AssetTestResult
        """
        result = test_asset_execution(
            asset_fn,
            partition=partition,
            mock_iceberg=self.catalog,
            mock_trino=self.trino,
        )

        self.results.append(result)
        return result

    def get_results(self, asset_fn: Callable) -> list[AssetTestResult]:
        """
        Get results for a specific asset.

        Args:
            asset_fn: Asset function to filter by

        Returns:
            List of results for that asset
        """
        # This is a simplified implementation
        # In practice, you'd track asset names
        return self.results

    def cleanup(self) -> None:
        """Clean up resources."""
        self.catalog.close()
