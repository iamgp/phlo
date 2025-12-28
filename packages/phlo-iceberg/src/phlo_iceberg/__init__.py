from phlo_iceberg.catalog import get_catalog
from phlo_iceberg.tables import (
    append_to_table,
    ensure_table,
    expire_snapshots,
    get_table_stats,
    merge_to_table,
    remove_orphan_files,
)

__all__ = [
    "append_to_table",
    "ensure_table",
    "expire_snapshots",
    "get_catalog",
    "get_table_stats",
    "merge_to_table",
    "remove_orphan_files",
]

# Dagster maintenance utilities available via:
# from phlo_iceberg.maintenance import get_maintenance_definitions
