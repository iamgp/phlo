"""Tests for table-store support metadata."""

from phlo.capabilities.interfaces import TableStoreSupport


def test_table_store_support_defaults_to_basic_writes() -> None:
    support = TableStoreSupport()

    assert support.supports_refs is False
    assert support.partition_transforms == frozenset({"identity"})
    assert support.supports_snapshots is False
    assert support.supports_compaction is False
    assert support.supports_vacuum is False


def test_table_store_support_reports_partition_transform_support() -> None:
    support = TableStoreSupport(partition_transforms=frozenset({"identity", "day"}))

    assert support.supports_partition_transform("identity") is True
    assert support.supports_partition_transform("bucket") is False
