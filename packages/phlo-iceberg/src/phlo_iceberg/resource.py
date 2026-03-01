from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pandera.pandas import DataFrameModel
from pyiceberg.catalog import Catalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table

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
    """Resource wrapper for the Nessie-backed Iceberg catalog."""

    ref: str = field(default_factory=lambda: get_settings().iceberg_nessie_ref)

    def get_catalog(self, override_ref: str | None = None) -> Catalog:
        """Return an Iceberg catalog client for the active branch.

        Args:
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Catalog: Configured Iceberg catalog instance.
        """
        branch = override_ref or self.ref
        return get_catalog(ref=branch)

    def schema_from_validation_schema(
        self, validation_schema: type[DataFrameModel] | type[Any]
    ) -> Schema:
        """Build an Iceberg schema from a validation model for ingestion flows."""
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

        Args:
            table_name: Fully qualified table name.
            schema: Iceberg table schema.
            partition_spec: Optional list of ``(field, transform)`` partition rules.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            Table: Existing or newly created Iceberg table.
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
        """Append parquet data into an Iceberg table.

        Args:
            table_name: Fully qualified table name.
            data_path: Path to parquet input data.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the append operation.
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
        """Merge parquet data into an Iceberg table using a unique key.

        Args:
            table_name: Fully qualified table name.
            data_path: Path to parquet input data.
            unique_key: Column used to match existing rows.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the merge operation.
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
        """Overwrite an Iceberg table with staged parquet data.

        Args:
            table_name: Fully qualified table name.
            data_path: Path to parquet input data.
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Write statistics from the overwrite operation.
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

        Args:
            table_name: Fully qualified table name.
            predicate: Filter expression (e.g. ``"status = 'inactive'"``).
            override_ref: Optional branch or tag to use instead of ``self.ref``.

        Returns:
            dict[str, int]: Delete statistics (rows_deleted is -1 as PyIceberg
            does not return a count).
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

        Not supported by PyIceberg — use Trino ``OPTIMIZE`` instead.
        """
        raise NotImplementedError("Compaction requires Spark or Trino; use Trino OPTIMIZE instead")

    def list_snapshots(self, *, table_name: str, limit: int = 10) -> list[dict]:
        """List recent table snapshots.

        Args:
            table_name: Fully qualified table name.
            limit: Maximum number of snapshots to return.

        Returns:
            list[dict]: Snapshot metadata dicts, most recent first.
        """
        return list_table_snapshots(table_name=table_name, limit=limit, ref=self.ref)

    def rollback_to_snapshot(self, *, table_name: str, snapshot_id: int | str) -> dict:
        """Roll back a table to a previous snapshot.

        Args:
            table_name: Fully qualified table name.
            snapshot_id: Target snapshot ID.

        Returns:
            dict: Contains ``rolled_back_to`` snapshot ID.
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

        Args:
            table_name: Fully qualified table name.
            retain_hours: Retention period in hours (default 168 = 7 days).

        Returns:
            dict: Combined results from snapshot expiration and orphan removal.
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
