"""
Mock Iceberg catalog backed by DuckDB for fast unit testing.

Implements a subset of PyIceberg's Catalog interface using an in-memory
DuckDB database, enabling tests to run without the full Iceberg/Nessie stack.

Example:
    >>> catalog = MockIcebergCatalog()
    >>> # Use with any schema dict like {"id": "int", "name": "string"}
    >>> table = catalog.create_table("raw.users", schema={"id": "int", "name": "string"})
    >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    >>> table.append(df)
    >>> result = table.scan().to_pandas()
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Optional, Sequence, Union

import duckdb
import pandas as pd


def _normalize_type(dtype: str) -> str:
    """
    Normalize type string to DuckDB type.
    
    Handles PyIceberg types, Python types, and plain strings.
    """
    dtype_str = str(dtype).lower()
    
    # Map PyIceberg/Pandera types to DuckDB types
    type_mapping = {
        "int32": "INTEGER",
        "int64": "BIGINT",
        "int": "INTEGER",
        "long": "BIGINT",
        "float": "FLOAT",
        "double": "DOUBLE",
        "string": "VARCHAR",
        "str": "VARCHAR",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
        "datetime": "TIMESTAMP",
        "object": "VARCHAR",
        "bytes": "BLOB",
    }
    
    for key, val in type_mapping.items():
        if key in dtype_str:
            return val
    
    # Default to VARCHAR for unknown types
    return "VARCHAR"


@dataclass
class MockTable:
    """
    Mock Iceberg table backed by DuckDB.

    Stores metadata in Python, actual data in DuckDB in-memory database.
    """

    name: str
    schema: Union[dict[str, str], Any]  # Dict or PyIceberg Schema
    _db: duckdb.DuckDBPyConnection
    _catalog: Optional[MockIcebergCatalog] = None

    def __post_init__(self) -> None:
        """Initialize table in DuckDB."""
        self._create_duckdb_table()

    def _create_duckdb_table(self) -> None:
        """Create the actual table in DuckDB."""
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Build CREATE TABLE statement from schema
        columns = []
        
        if isinstance(self.schema, dict):
            # Simple dict schema: {"col_name": "type_string"}
            for col_name, col_type in self.schema.items():
                duckdb_type = _normalize_type(col_type)
                columns.append(f"{col_name} {duckdb_type}")
        else:
            # PyIceberg Schema object
            for field in self.schema.fields:
                duckdb_type = _normalize_type(str(field.type))
                nullable = "NULL" if field.optional else "NOT NULL"
                columns.append(f"{field.name} {duckdb_type} {nullable}")

        create_stmt = f"CREATE TABLE {full_name} ({', '.join(columns)})"
        try:
            self._db.execute(create_stmt)
        except duckdb.CatalogException:
            # Table already exists
            pass

    def append(self, df: pd.DataFrame) -> None:
        """
        Append DataFrame to table.

        Args:
            df: Data to append

        Raises:
            ValueError: If schema doesn't match
        """
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Validate schema
        self._validate_schema(df)

        # Insert into DuckDB
        self._db.from_df(df).insert_into(full_name)

    def overwrite(self, df: pd.DataFrame) -> None:
        """
        Replace table contents with DataFrame.

        Args:
            df: Data to replace with
        """
        namespace, table_name = self.name.split(".")
        full_name = f"{namespace}_{table_name}"

        # Validate schema
        self._validate_schema(df)

        # Truncate and insert
        self._db.execute(f"DELETE FROM {full_name}")
        self._db.from_df(df).insert_into(full_name)

    def scan(self) -> MockTableScan:
        """
        Scan table data.

        Returns:
            MockTableScan object for querying
        """
        return MockTableScan(self)

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """Validate DataFrame schema against table schema."""
        df_cols = set(df.columns)
        
        if isinstance(self.schema, dict):
            table_cols = set(self.schema.keys())
        else:
            # PyIceberg Schema
            table_cols = {field.name for field in self.schema.fields}

        if df_cols != table_cols:
            missing = table_cols - df_cols
            extra = df_cols - table_cols
            msg = f"Schema mismatch for {self.name}"
            if missing:
                msg += f"\nMissing columns: {missing}"
            if extra:
                msg += f"\nExtra columns: {extra}"
            raise ValueError(msg)

    @property
    def full_name(self) -> str:
        """Get full table name with namespace."""
        namespace, table_name = self.name.split(".")
        return f"{namespace}_{table_name}"


class MockTableScan:
    """Results from scanning a MockTable."""

    def __init__(self, table: MockTable) -> None:
        """Initialize scan for a table."""
        self.table = table

    def to_pandas(self) -> pd.DataFrame:
        """
        Execute scan and return as pandas DataFrame.

        Returns:
            Query results as DataFrame
        """
        query = f"SELECT * FROM {self.table.full_name}"
        result = self.table._db.execute(query).fetchall()

        if not result:
            # Return empty DataFrame with correct schema
            if isinstance(self.table.schema, dict):
                return pd.DataFrame({col: [] for col in self.table.schema.keys()})
            else:
                return pd.DataFrame(
                    {field.name: [] for field in self.table.schema.fields}
                )

        # Get column names from cursor description
        col_names = [desc[0] for desc in self.table._db.description]
        return pd.DataFrame(result, columns=col_names)

    def to_arrow(self) -> Any:
        """
        Execute scan and return as PyArrow Table.

        Returns:
            Query results as Arrow Table
        """
        try:
            import pyarrow as pa
            df = self.to_pandas()
            return pa.Table.from_pandas(df)
        except ImportError:
            raise ImportError("PyArrow required for to_arrow(). Install: pip install pyarrow")


class MockIcebergCatalog:
    """
    In-memory Iceberg catalog mock using DuckDB backend.

    Implements a subset of PyIceberg's Catalog interface for testing.
    Tables are stored in DuckDB with metadata tracked in Python dicts.

    Example:
        >>> catalog = MockIcebergCatalog()
        >>> schema = {"id": "int", "name": "string"}
        >>> table = catalog.create_table("raw.users", schema=schema)
        >>> df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> table.append(df)
    """

    def __init__(self) -> None:
        """Initialize in-memory DuckDB catalog."""
        self._db = duckdb.connect(":memory:")
        self._tables: dict[str, MockTable] = {}
        self._namespaces: set[str] = set()

        # Create default namespaces
        for ns in ["raw", "bronze", "silver", "gold", "marts"]:
            self.create_namespace(ns)

    def create_namespace(self, namespace: str) -> None:
        """
        Create a namespace.

        Args:
            namespace: Namespace name

        Raises:
            ValueError: If namespace already exists
        """
        if namespace in self._namespaces:
            raise ValueError(f"Namespace {namespace} already exists")

        self._namespaces.add(namespace)

        # Create schema in DuckDB
        try:
            self._db.execute(f'CREATE SCHEMA "{namespace}"')
        except duckdb.CatalogException:
            # Schema might already exist
            pass

    def drop_namespace(self, namespace: str) -> None:
        """
        Drop a namespace.

        Args:
            namespace: Namespace name
        """
        self._namespaces.discard(namespace)
        try:
            self._db.execute(f'DROP SCHEMA IF EXISTS "{namespace}"')
        except duckdb.CatalogException:
            pass

    def create_table(
        self,
        identifier: str,
        schema: Union[dict[str, str], Any],
        partition_spec: Optional[Sequence[tuple[str, str]]] = None,
    ) -> MockTable:
        """
        Create a new table.

        Args:
            identifier: Table name (namespace.table)
            schema: Schema dict like {"col": "type"} or PyIceberg Schema
            partition_spec: Optional partitioning (not fully supported)

        Returns:
            MockTable instance

        Raises:
            ValueError: If table already exists
        """
        if identifier in self._tables:
            raise ValueError(f"Table {identifier} already exists")

        # Extract namespace and ensure it exists
        namespace = identifier.split(".")[0]
        if namespace not in self._namespaces:
            self.create_namespace(namespace)

        table = MockTable(
            name=identifier,
            schema=schema,
            _db=self._db,
            _catalog=self,
        )

        self._tables[identifier] = table
        return table

    def load_table(self, identifier: str) -> MockTable:
        """
        Load an existing table.

        Args:
            identifier: Table name (namespace.table)

        Returns:
            MockTable instance

        Raises:
            ValueError: If table doesn't exist
        """
        if identifier not in self._tables:
            raise ValueError(f"Table {identifier} not found")

        return self._tables[identifier]

    def drop_table(self, identifier: str) -> None:
        """
        Drop a table.

        Args:
            identifier: Table name (namespace.table)
        """
        if identifier in self._tables:
            table = self._tables.pop(identifier)
            try:
                self._db.execute(f"DROP TABLE IF EXISTS {table.full_name}")
            except duckdb.CatalogException:
                pass

    def list_tables(self, namespace: str) -> list[str]:
        """
        List tables in a namespace.

        Args:
            namespace: Namespace name

        Returns:
            List of table identifiers
        """
        return [
            identifier
            for identifier in self._tables.keys()
            if identifier.startswith(f"{namespace}.")
        ]

    def list_namespaces(self) -> list[str]:
        """
        List all namespaces.

        Returns:
            List of namespace names
        """
        return sorted(self._namespaces)

    def rename_table(self, old_identifier: str, new_identifier: str) -> None:
        """
        Rename a table.

        Args:
            old_identifier: Current table name
            new_identifier: New table name
        """
        if old_identifier not in self._tables:
            raise ValueError(f"Table {old_identifier} not found")

        table = self._tables.pop(old_identifier)
        table.name = new_identifier
        self._tables[new_identifier] = table

        # Rename in DuckDB
        old_full = old_identifier.replace(".", "_")
        new_full = new_identifier.replace(".", "_")
        try:
            self._db.execute(f"ALTER TABLE {old_full} RENAME TO {new_full}")
        except duckdb.CatalogException:
            pass

    def table_exists(self, identifier: str) -> bool:
        """
        Check if a table exists.

        Args:
            identifier: Table name (namespace.table)

        Returns:
            True if table exists
        """
        return identifier in self._tables

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """
        Context manager for transactions (no-op in mock).

        Yields:
            None
        """
        try:
            yield
        except Exception:
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self._db:
            self._db.close()

    def __enter__(self) -> MockIcebergCatalog:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
