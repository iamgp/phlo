"""IcebergResource dataclass for asset/resource access.

This module provides the ``IcebergResource`` dataclass, which serves as a
high-level interface for Iceberg operations within Dagster assets and resources.
It wraps table operations, snapshot management, and schema conversion in a
convenient API suitable for use as a Dagster resource.

The resource is designed to work with Phlo's capability system and supports
branching via Nessie references.

Example:
    Using IcebergResource in a Dagster asset::

        from dagster import asset
        from phlo_iceberg import IcebergResource

        @asset
        def processed_events(iceberg: IcebergResource):
            # Ensure table exists
            from pyiceberg.schema import Schema
            from pyiceberg.types import NestedField, LongType, StringType

            schema = Schema(
                NestedField(1, "id", LongType(), required=True),
                NestedField(2, "data", StringType(), required=False),
            )
            iceberg.ensure_table("raw.events", schema=schema)

            # Append data
            result = iceberg.append_parquet(
                table_name="raw.events",
                data_path="/data/events.parquet"
            )
            return result

    Resource configuration::

        from dagster import Definitions
        from phlo_iceberg import IcebergResource

        defs = Definitions(
            resources={
                "iceberg": IcebergResource(ref="main")
            }
        )

"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pandera.pandas import DataFrameModel
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

from phlo.capabilities.interfaces import TableStoreSupport
from phlo.logging import get_logger
from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.settings import get_settings
from phlo_iceberg.tables import (
    append_to_table,
    delete_rows_from_table,
    ensure_table,
    expire_snapshots,
    list_table_snapshots,
    merge_to_table,
    overwrite_table,
    remove_orphan_files,
    rollback_table_to_snapshot,
)

logger = get_logger(__name__)


@dataclass
class IcebergResource:
    """Resource wrapper for Iceberg REST catalog operations.

    Provides a high-level interface for common Iceberg table operations
    including data ingestion (append, merge, overwrite), snapshot management,
    and schema conversion. Designed for use as a Dagster resource.

    Attributes:
        ref: Nessie branch/tag reference for all operations. Defaults to
            the value from settings (typically ``main``).

    Example:
        Basic resource usage::

            iceberg = IcebergResource(ref="main")

            # Work with catalog
            catalog = iceberg.get_catalog()

            # Convert Pandera schema
            schema = iceberg.schema_from_validation_schema(MyPanderaModel)

            # Ensure table exists
            table = iceberg.ensure_table("raw.events", schema=schema)

            # Append data
            result = iceberg.append_parquet("raw.events", "/data/events.parquet")
            print(f"Inserted {result['rows_inserted']} rows")

    """

    ref: str = field(default_factory=lambda: get_settings().iceberg_default_ref)

    @property
    def support(self) -> TableStoreSupport:
        """Return Iceberg table-store support metadata."""
        return TableStoreSupport(
            supports_refs=True,
            partition_transforms=frozenset({"identity", "day", "hour", "month", "year"}),
            supports_snapshots=True,
            supports_compaction=False,
            supports_vacuum=True,
        )

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """Return an Iceberg catalog client for the active branch.

        Args:
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Catalog: Configured PyIceberg catalog instance.

        Example:
            Access catalog directly::

                iceberg = IcebergResource(ref="main")
                catalog = iceberg.get_catalog()

                # Access low-level catalog methods
                table = catalog.load_table("raw.events")

                # Or use different branch
                dev_catalog = iceberg.get_catalog(override_ref="dev-branch")

        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> Schema:
        """Convert a Pandera validation model to an Iceberg schema.

        Useful for ingestion flows where data is validated using Pandera
        models before being written to Iceberg.

        Args:
            validation_schema: Pandera DataFrameModel class to convert.

        Returns:
            Schema: Iceberg schema equivalent to the Pandera model.

        Raises:
            SchemaConversionError: If the Pandera schema cannot be converted.

        Example:
            Convert Pandera model to Iceberg schema::

                from pandera import DataFrameModel, Column, Int64, String

                class UserSchema(DataFrameModel):
                    id: Column[Int64]
                    name: Column[String]

                iceberg = IcebergResource()
                schema = iceberg.schema_from_validation_schema(UserSchema)
                table = iceberg.ensure_table("raw.users", schema=schema)

        """
        from phlo_iceberg.schema_conversion import pandera_to_iceberg

        return pandera_to_iceberg(validation_schema)

    def ensure_table(
        self,
        table_name: str,
        schema: Schema,
        partition_spec: Sequence[tuple[str, str]] | None = None,
        override_ref: str | None = None,
    ) -> Table:
        """Ensure a table exists and return its handle.

        Creates the table if it doesn't exist, otherwise returns the existing table.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            schema: Iceberg table schema.
            partition_spec: Optional list of ``(field, transform)`` partition rules.
                Supported transforms: ``identity``, ``day``, ``hour``, ``month``, ``year``.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Table: Existing or newly created Iceberg table handle.

        Example:
            Ensure table with partitioning::

                from pyiceberg.schema import Schema
                from pyiceberg.types import NestedField, LongType, TimestamptzType

                schema = Schema(
                    NestedField(1, "id", LongType(), required=True),
                    NestedField(2, "ts", TimestamptzType(), required=True),
                )

                table = iceberg.ensure_table(
                    "raw.events",
                    schema=schema,
                    partition_spec=[("ts", "day")]
                )

        """
        branch = override_ref or self.ref
        return ensure_table(
            table_name=table_name,
            schema=schema,
            partition_spec=list(partition_spec) if partition_spec else None,
            ref=branch,
        )

    def append_parquet(
        self, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Append Parquet data into an Iceberg table.

        Reads data from a Parquet file or directory and appends it to the
        specified table. Automatically aligns schema and handles missing columns.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the append operation:
                - ``rows_inserted``: Number of rows appended.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during append.

        Example:
            Simple append::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events_2024-01-01.parquet"
                )

            Append to specific branch::

                result = iceberg.append_parquet(
                    table_name="raw.events",
                    data_path="/data/events.parquet",
                    override_ref="dev-branch"
                )

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_append_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = append_to_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_append_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_append_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def merge_parquet(
        self,
        table_name: str,
        data_path: str,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge (upsert) Parquet data into an Iceberg table using a unique key.

        Deletes existing rows with matching unique key values, then inserts
        the new data. This implements an upsert pattern useful for
        idempotent data loads.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            unique_key: Column name used to identify and match existing rows.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the merge operation:
                - ``rows_deleted``: Approximate count of rows deleted.
                - ``rows_inserted``: Number of rows inserted.

        Raises:
            Exception: Re-raises any errors during merge.

        Example:
            Upsert user data by ID::

                result = iceberg.merge_parquet(
                    table_name="raw.users",
                    data_path="/data/user_updates.parquet",
                    unique_key="user_id"
                )
                print(f"Updated ~{result['rows_deleted']} rows")
                print(f"Inserted {result['rows_inserted']} rows")

        Note:
            The ``rows_deleted`` count is an approximation because Iceberg
            doesn't report the actual number of rows deleted during the operation.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_merge_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
        )
        try:
            result = merge_to_table(
                table_name=table_name,
                data_path=data_path,
                unique_key=unique_key,
                ref=branch,
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_merge_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                unique_key=unique_key,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_merge_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            unique_key=unique_key,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def overwrite_parquet(
        self, *, table_name: str, data_path: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Overwrite an Iceberg table with staged Parquet data.

        Replaces all existing data with the new data, creating a new snapshot.
        Previous data remains accessible via snapshot history until snapshots
        are expired.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            data_path: Path to Parquet input data (file or directory).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation:
                - ``rows_inserted``: Number of rows in replacement data.
                - ``rows_deleted``: Always 0.

        Raises:
            Exception: Re-raises any errors during overwrite.

        Example:
            Regenerate summary table::

                result = iceberg.overwrite_parquet(
                    table_name="analytics.daily_summary",
                    data_path="/data/regenerated_summary.parquet"
                )
                print(f"Table now has {result['rows_inserted']} rows")

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_overwrite_requested",
            table_name=table_name,
            ref=branch,
            source=data_path,
        )
        try:
            result = overwrite_table(table_name=table_name, data_path=data_path, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_overwrite_failed",
                table_name=table_name,
                ref=branch,
                source=data_path,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_overwrite_completed",
            table_name=table_name,
            ref=branch,
            source=data_path,
            rows_inserted=result.get("rows_inserted", 0),
            rows_deleted=result.get("rows_deleted", 0),
        )
        return result

    def delete_rows(
        self, *, table_name: str, predicate: str, override_ref: str | None = None
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression.

        Uses Iceberg's delete operation with a SQL-style predicate expression.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            predicate: Filter expression string (e.g., ``"status = 'inactive'"``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Delete statistics:
                - ``rows_deleted``: Always -1 (PyIceberg doesn't return count).

        Raises:
            Exception: Re-raises any errors during deletion.

        Example:
            Delete old records::

                iceberg.delete_rows(
                    table_name="raw.events",
                    predicate="event_time < '2024-01-01'"
                )

            Delete by status::

                iceberg.delete_rows(
                    table_name="raw.users",
                    predicate="account_status = 'deleted'"
                )

        Note:
            PyIceberg does not return the number of rows deleted, so
            ``rows_deleted`` is always -1.

        """
        branch = override_ref or self.ref
        logger.info(
            "iceberg_resource_delete_rows_requested",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        try:
            result = delete_rows_from_table(table_name=table_name, predicate=predicate, ref=branch)
        except Exception as exc:
            logger.error(
                "iceberg_resource_delete_rows_failed",
                table_name=table_name,
                ref=branch,
                predicate=predicate,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_delete_rows_completed",
            table_name=table_name,
            ref=branch,
            predicate=predicate,
        )
        return result

    def compact(self, *, table_name: str, override_ref: str | None = None) -> dict[str, object]:
        """Compact small files in a table.

        Warning:
            Not supported by PyIceberg directly. Use Trino ``OPTIMIZE`` command
            instead for file compaction.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Raises:
            NotImplementedError: Always raised. Use Trino for compaction.

        See Also:
            Trino Iceberg connector: https://trino.io/docs/current/connector/iceberg.html

        """
        raise NotImplementedError("Compaction requires Spark or Trino; use Trino OPTIMIZE instead")

    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table snapshots.

        Retrieves snapshot metadata including operation type, timestamp, and
        summary statistics. Results are sorted by timestamp (most recent first).

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            limit: Maximum number of snapshots to return (default: 10).

        Returns:
            list[dict]: Snapshot metadata dicts, most recent first. Each dict
                contains ``snapshot_id``, ``timestamp_ms``, ``operation``, and
                ``summary`` fields.

        Example:
            Review table history::

                snapshots = iceberg.list_snapshots(
                    table_name="raw.events",
                    limit=5
                )
                for snap in snapshots:
                    print(f"{snap['snapshot_id']}: {snap['operation']}")

        """
        return list_table_snapshots(table_name=table_name, limit=limit, ref=self.ref)

    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous snapshot.

        Restores the table to a specific point in time using the snapshot ID.
        Creates a new snapshot that points to the historical state.

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            snapshot_id: Target snapshot ID (can be int or string).

        Returns:
            dict: Rollback result containing ``rolled_back_to`` snapshot ID.

        Raises:
            Exception: Re-raises any errors during rollback.

        Example:
            Rollback after bad data load::

                # Find snapshot to restore
                snapshots = iceberg.list_snapshots(table_name="raw.events", limit=10)
                target_id = snapshots[1]["snapshot_id"]  # Previous snapshot

                # Rollback
                result = iceberg.rollback_to_snapshot(
                    table_name="raw.events",
                    snapshot_id=target_id
                )
                print(f"Rolled back to snapshot {result['rolled_back_to']}")

        Warning:
            Rollback creates a new snapshot. The newer snapshots are not
            deleted and can still be accessed if needed.

        """
        logger.info(
            "iceberg_resource_rollback_requested",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        try:
            result = rollback_table_to_snapshot(
                table_name=table_name, snapshot_id=int(snapshot_id), ref=self.ref
            )
        except Exception as exc:
            logger.error(
                "iceberg_resource_rollback_failed",
                table_name=table_name,
                snapshot_id=snapshot_id,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
        logger.info(
            "iceberg_resource_rollback_completed",
            table_name=table_name,
            snapshot_id=snapshot_id,
        )
        return result

    def vacuum(self, *, table_name: str, retain_hours: int = 168) -> dict:
        """Remove expired snapshots and orphan files.

        Performs table maintenance by:
        1. Expiring snapshots older than the retention period
        2. Removing orphan files not referenced by any remaining snapshot

        Args:
            table_name: Fully qualified table name (``namespace.table``).
            retain_hours: Retention period in hours (default: 168 = 7 days).
                Snapshots newer than this will be retained.

        Returns:
            dict: Maintenance results containing:
                - ``deleted_snapshots``: Number of expired snapshots removed.
                - ``orphan_files_removed``: Number of orphan files deleted.

        Raises:
            Exception: Re-raises any errors during maintenance.

        Example:
            Weekly maintenance::

                result = iceberg.vacuum(
                    table_name="raw.events",
                    retain_hours=168  # Keep 7 days
                )
                print(f"Removed {result['deleted_snapshots']} snapshots")
                print(f"Removed {result['orphan_files_removed']} orphan files")

        Warning:
            Orphan file removal permanently deletes data files from storage.
            Ensure no concurrent writes are happening during vacuum operations.

        """
        logger.info(
            "iceberg_resource_vacuum_requested",
            table_name=table_name,
            retain_hours=retain_hours,
        )
        snap_result = expire_snapshots(
            table_name=table_name, older_than_hours=retain_hours, ref=self.ref
        )
        orphan_result = remove_orphan_files(
            table_name=table_name, older_than_hours=retain_hours, dry_run=False, ref=self.ref
        )
        result = {
            "deleted_snapshots": snap_result["deleted_snapshots"],
            "orphan_files_removed": orphan_result["orphan_count"],
        }
        logger.info(
            "iceberg_resource_vacuum_completed",
            table_name=table_name,
            **result,
        )
        return result
