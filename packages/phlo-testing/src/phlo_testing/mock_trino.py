"""
Mock Trino resource backed by DuckDB for testing.

Provides a mock implementation of TrinoResource that uses DuckDB as the backend,
enabling SQL testing without requiring a real Trino server.

Example:
    >>> trino = MockTrinoResource()
    >>> cursor = trino.cursor()
    >>> cursor.execute("CREATE TABLE test AS SELECT 1 as id")
    >>> result = cursor.execute("SELECT * FROM test")
    >>> print(cursor.fetchall())
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Literal, Optional

import duckdb
import pandas as pd


class MockCursor:
    """
    Mock Trino cursor backed by DuckDB.

    Implements the DB-API 2.0 cursor interface.
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """
        Initialize cursor.

        Args:
            connection: DuckDB connection
        """
        self._connection = connection
        self._result = None
        self._description = None
        self._row_index = 0

    def execute(self, query: str, params: Optional[tuple] = None) -> MockCursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Optional parameters (not fully supported)

        Returns:
            Self for method chaining

        Raises:
            Exception: If query fails
        """
        try:
            # Translate Trino SQL to DuckDB if needed
            query = self._translate_query(query)

            # Execute query
            result = self._connection.execute(query)
            self._result = result

            # Get column names and types
            try:
                # Try to get columns from result
                cols = result.columns
                if cols:
                    self._description = [
                        (name, "VARCHAR")  # Simplified type mapping
                        for name in cols
                    ]
                else:
                    self._description = None
            except (AttributeError, TypeError):
                # Fallback if no columns attribute
                self._description = None

            self._row_index = 0
            return self

        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

    def fetchall(self) -> list[tuple]:
        """
        Fetch all results.

        Returns:
            List of tuples representing rows
        """
        if self._result is None:
            return []

        rows = self._result.fetchall()
        self._row_index = len(rows)
        return rows

    def fetchone(self) -> Optional[tuple]:
        """
        Fetch one result.

        Returns:
            Single row as tuple, or None if no more rows
        """
        if self._result is None:
            return None

        row = self._result.fetchone()
        if row is not None:
            self._row_index += 1
        return row

    def fetchmany(self, size: int = 1) -> list[tuple]:
        """
        Fetch multiple results.

        Args:
            size: Number of rows to fetch

        Returns:
            List of tuples
        """
        if self._result is None:
            return []

        rows = self._result.fetchmany(size)
        self._row_index += len(rows)
        return rows

    def fetchdf(self) -> pd.DataFrame:
        """
        Fetch all results as DataFrame.

        Returns:
            DataFrame with query results
        """
        if self._result is None:
            return pd.DataFrame()

        return self._result.df()

    @property
    def description(self) -> Optional[list]:
        """
        Get column metadata.

        Returns:
            List of column descriptors
        """
        return self._description

    @property
    def rowcount(self) -> int:
        """
        Get number of affected rows.

        Returns:
            Row count
        """
        return self._row_index if self._result else -1

    def close(self) -> None:
        """Close cursor."""
        self._result = None
        self._description = None

    @staticmethod
    def _translate_query(query: str) -> str:
        """
        Translate Trino SQL to DuckDB SQL.

        Args:
            query: Trino SQL query

        Returns:
            DuckDB SQL query

        Most Trino SQL is compatible with DuckDB, but we handle some
        common differences here.
        """
        # Replace common Trino functions with DuckDB equivalents

        # For now, most Trino queries work directly in DuckDB
        return query


class MockConnection:
    """
    Mock Trino connection backed by DuckDB.

    Implements the DB-API 2.0 connection interface.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        user: str = "user",
        catalog: str = "memory",
        schema: Optional[str] = None,
    ) -> None:
        """
        Initialize connection.

        Args:
            host: Host (ignored, for compatibility)
            port: Port (ignored, for compatibility)
            user: Username (ignored, for compatibility)
            catalog: Catalog name (ignored, for compatibility)
            schema: Schema name (ignored, for compatibility)
        """
        self._db = duckdb.connect(":memory:")
        self.catalog = catalog
        self.schema = schema
        self._tables: dict[str, pd.DataFrame] = {}

    def cursor(self) -> MockCursor:
        """
        Create a cursor.

        Returns:
            MockCursor instance
        """
        return MockCursor(self._db)

    def execute(self, query: str) -> MockCursor:
        """
        Execute a query and return cursor.

        Args:
            query: SQL query

        Returns:
            MockCursor with results
        """
        cursor = self.cursor()
        cursor.execute(query)
        return cursor

    def commit(self) -> None:
        """Commit transaction (no-op in mock)."""
        pass

    def rollback(self) -> None:
        """Rollback transaction (no-op in mock)."""
        pass

    def close(self) -> None:
        """Close connection."""
        if self._db:
            self._db.close()

    def __enter__(self) -> MockConnection:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


class MockTrinoResource:
    """
    Mock Trino resource for testing.

    Drop-in replacement for TrinoResource that uses DuckDB as backend.
    Enables SQL testing without a real Trino server.

    Example:
        >>> trino = MockTrinoResource()
        >>> cursor = trino.cursor()
        >>> cursor.execute("SELECT 1 as id")
        >>> results = cursor.fetchall()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        user: str = "dagster",
        catalog: str = "memory",
        trino_schema: Optional[str] = None,
    ) -> None:
        """
        Initialize mock Trino resource.

        Args:
            host: Host (ignored, for compatibility)
            port: Port (ignored, for compatibility)
            user: Username (ignored, for compatibility)
            catalog: Catalog name (ignored, for compatibility)
            trino_schema: Schema name (ignored, for compatibility)
        """
        self.host = host
        self.port = port
        self.user = user
        self.catalog = catalog
        self.trino_schema = trino_schema
        self._db = duckdb.connect(":memory:")
        self._tables: dict[str, pd.DataFrame] = {}

    def get_connection(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> MockConnection:
        """
        Get a connection.

        Args:
            schema: Schema to use
            branch: Branch (ignored, for compatibility)

        Returns:
            MockConnection instance
        """
        return MockConnection(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=schema or self.trino_schema,
        )

    @contextmanager
    def connection(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> Iterator[MockConnection]:
        """
        Context manager for a connection.

        Args:
            schema: Schema to use
            branch: Branch (ignored, for compatibility)

        Yields:
            MockConnection instance
        """
        conn = self.get_connection(schema=schema, branch=branch)
        try:
            yield conn
        finally:
            conn.close()

    def cursor(
        self,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> MockCursor:
        """
        Get a cursor.

        Args:
            schema: Schema to use
            branch: Branch (ignored, for compatibility)

        Returns:
            MockCursor instance
        """
        return MockCursor(self._db)

    def execute(
        self,
        query: str,
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> list[tuple]:
        """
        Execute a query.

        Args:
            query: SQL query
            schema: Schema to use
            branch: Branch (ignored, for compatibility)

        Returns:
            List of result tuples
        """
        cursor = self.cursor(schema=schema, branch=branch)
        cursor.execute(query)
        return cursor.fetchall()

    def query_with_schema(
        self,
        query: str,
        schema_class: type[Any],
        schema: Optional[str] = None,
        branch: Optional[Literal["main", "dev"]] = None,
    ) -> pd.DataFrame:
        """
        Execute a query and apply types from a Pandera schema.

        This eliminates manual type conversion boilerplate in quality checks.
        The DataFrame types are automatically coerced based on schema annotations.

        Args:
            query: SQL query
            schema_class: Pandera DataFrameModel class with type annotations
            schema: Schema to use
            branch: Branch (ignored, for compatibility)

        Returns:
            DataFrame with types coerced according to schema

        Example:
            from phlo_testing import MockTrinoResource
            from workflows.schemas.glucose import FactGlucoseReadings

            trino = MockTrinoResource()
            df = trino.query_with_schema(
                "SELECT * FROM gold.fct_glucose_readings",
                FactGlucoseReadings,
            )
            # Types are now correct for validation
        """
        from phlo_trino.type_mapping import apply_schema_types

        cursor = self.cursor(schema=schema, branch=branch)
        cursor.execute(query)
        df = cursor.fetchdf()

        # Apply schema-aware type conversions
        return apply_schema_types(df, schema_class)

    def load_table(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Load a DataFrame as a test table.

        Useful for setting up test data.

        Args:
            table_name: Name of table to create
            df: DataFrame with data

        Example:
            >>> trino = MockTrinoResource()
            >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
            >>> trino.load_table("test.users", df)
            >>> cursor = trino.cursor()
            >>> cursor.execute("SELECT * FROM test.users")
        """
        self._tables[table_name] = df

        # Register DataFrame with DuckDB
        self._db.register(table_name.replace(".", "_"), df)

    def get_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get a loaded test table.

        Args:
            table_name: Name of table

        Returns:
            DataFrame if table exists, None otherwise
        """
        return self._tables.get(table_name)

    def list_tables(self, schema: Optional[str] = None) -> list[str]:
        """
        List available tables.

        Args:
            schema: Schema to list (ignored)

        Returns:
            List of table names
        """
        return list(self._tables.keys())

    def close(self) -> None:
        """Close all connections."""
        if self._db:
            self._db.close()

    def __enter__(self) -> MockTrinoResource:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
