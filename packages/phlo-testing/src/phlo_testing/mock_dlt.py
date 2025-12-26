"""
Mock DLT sources for testing without API calls.

Provides mock implementations of DLT sources that return predefined data,
enabling tests to run without external dependencies or network calls.

Example:
    >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    >>> source = mock_dlt_source(data, resource_name="users")
    >>> for record in source:
    ...     print(record)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

import pandas as pd


@dataclass
class MockDLTResource:
    """
    Mock DLT resource that yields predefined data.

    Mimics the interface of a DLT resource but returns fixed data
    instead of fetching from an API.
    """

    name: str
    data: list[dict[str, Any]]
    _index: int = 0

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over resource data."""
        self._index = 0
        return self

    def __next__(self) -> dict[str, Any]:
        """Get next record."""
        if self._index >= len(self.data):
            raise StopIteration
        record = self.data[self._index]
        self._index += 1
        return record

    @property
    def resources(self) -> dict[str, Any]:
        """Get resource metadata."""
        return {
            self.name: {
                "name": self.name,
                "type": "resource",
                "columns": self._infer_schema(),
            }
        }

    def _infer_schema(self) -> dict[str, str]:
        """Infer schema from data."""
        if not self.data:
            return {}

        first_record = self.data[0]
        schema = {}

        for key, value in first_record.items():
            if isinstance(value, int):
                schema[key] = "bigint"
            elif isinstance(value, float):
                schema[key] = "double"
            elif isinstance(value, bool):
                schema[key] = "boolean"
            elif isinstance(value, str):
                schema[key] = "text"
            elif isinstance(value, pd.Timestamp) or hasattr(value, "isoformat"):
                schema[key] = "timestamp"
            else:
                schema[key] = "text"

        return schema


@dataclass
class MockDLTSource:
    """
    Mock DLT source with multiple resources.

    Mimics the interface of a DLT source but returns fixed data
    instead of fetching from an API. Supports multiple resources.
    """

    resources: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    _current_resource: str | None = None
    _current_index: int = 0

    def add_resource(self, name: str, data: list[dict[str, Any]]) -> MockDLTResource:
        """
        Add a resource to the source.

        Args:
            name: Resource name
            data: List of records

        Returns:
            MockDLTResource instance
        """
        self.resources[name] = data
        return MockDLTResource(name=name, data=data)

    def get_resource(self, name: str) -> MockDLTResource:
        """
        Get a resource by name.

        Args:
            name: Resource name

        Returns:
            MockDLTResource instance

        Raises:
            ValueError: If resource doesn't exist
        """
        if name not in self.resources:
            raise ValueError(f"Resource {name} not found")

        return MockDLTResource(name=name, data=self.resources[name])

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over all resources."""
        for resource_name, data in self.resources.items():
            for record in data:
                yield record

    def for_each(self, func: Any) -> None:
        """
        Apply a function to each record.

        Args:
            func: Function to apply (for dlt compatibility)
        """
        for record in self:
            func(record)


def mock_dlt_source(
    data: list[dict[str, Any]],
    resource_name: str = "default",
) -> MockDLTResource:
    """
    Create a mock DLT source with a single resource.

    Drop-in replacement for `dlt.resource()` that returns predefined data
    without making API calls.

    Args:
        data: List of records to return
        resource_name: Name of the resource

    Returns:
        MockDLTResource instance

    Example:
        >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> source = mock_dlt_source(data, resource_name="users")
        >>> for record in source:
        ...     print(record)
        {"id": 1, "name": "Alice"}
        {"id": 2, "name": "Bob"}
    """
    return MockDLTResource(name=resource_name, data=data)


def mock_dlt_source_multi(
    resources: dict[str, list[dict[str, Any]]],
) -> MockDLTSource:
    """
    Create a mock DLT source with multiple resources.

    Args:
        resources: Dict mapping resource names to data lists

    Returns:
        MockDLTSource instance

    Example:
        >>> source = mock_dlt_source_multi({
        ...     "users": [{"id": 1, "name": "Alice"}],
        ...     "orders": [{"order_id": 1, "user_id": 1}],
        ... })
        >>> for record in source:
        ...     print(record)
    """
    mock_source = MockDLTSource()
    for name, data in resources.items():
        mock_source.add_resource(name, data)
    return mock_source


class MockDLTError(Exception):
    """Exception for simulating DLT errors."""

    pass


def mock_dlt_source_with_error(
    data: list[dict[str, Any]],
    resource_name: str = "default",
    error_after: int | None = None,
    error_message: str = "Mock DLT error",
) -> MockDLTResource:
    """
    Create a mock DLT source that raises an error after N records.

    Useful for testing error handling in ingestion pipelines.

    Args:
        data: List of records to return before error
        resource_name: Name of the resource
        error_after: Number of records before error (None = no error)
        error_message: Error message to raise

    Returns:
        MockDLTResource instance

    Example:
        >>> source = mock_dlt_source_with_error(
        ...     [{"id": 1}, {"id": 2}],
        ...     error_after=1,
        ...     error_message="API rate limit exceeded"
        ... )
        >>> records = list(source)  # Raises after 1 record
    """

    class ErrorRaisingResource(MockDLTResource):
        """Resource that raises an error after N records."""

        def __next__(self) -> dict[str, Any]:
            if error_after is not None and self._index >= error_after:
                raise MockDLTError(error_message)
            return super().__next__()

    return ErrorRaisingResource(name=resource_name, data=data)


def mock_dlt_pipeline(
    data: dict[str, list[dict[str, Any]]],
) -> MockDLTSource:
    """
    Create a mock DLT pipeline with multiple resources.

    Convenience function for creating a complete mock pipeline.

    Args:
        data: Dict mapping table names to records

    Returns:
        MockDLTSource instance

    Example:
        >>> pipeline = mock_dlt_pipeline({
        ...     "users": [{"id": 1, "name": "Alice"}],
        ...     "orders": [{"order_id": 1, "user_id": 1}],
        ... })
    """
    return mock_dlt_source_multi(data)


def create_mock_dlt_dataframe(
    resource: MockDLTResource,
) -> pd.DataFrame:
    """
    Convert mock DLT resource to pandas DataFrame.

    Helper for testing data transformations.

    Args:
        resource: MockDLTResource instance

    Returns:
        DataFrame with resource data

    Example:
        >>> source = mock_dlt_source([{"id": 1}, {"id": 2}])
        >>> df = create_mock_dlt_dataframe(source)
    """
    return pd.DataFrame(list(resource))
