"""Quality check naming + metadata contract.

This module defines a small contract for asset checks so downstream consumers (e.g. Observatory)
can render results consistently without special-casing check implementations.

Contract
--------

Naming:
- Pandera schema contract check name: ``pandera_contract``
- dbt test check name: ``dbt__<test_type>__<target>``

Severity policy
---------------

- Pandera schema contract checks are blocking and emit ``ERROR`` on failure.
- dbt tests default to ``ERROR`` for ``not_null``, ``unique``, and ``relationships``; other test
  types default to ``WARN``.
- dbt tag overrides:
  - ``tag:blocking`` forces ``ERROR``
  - ``tag:warn`` or ``tag:anomaly`` forces ``WARN``

Partition semantics
-------------------

- If a Dagster run provides a partition key, checks are scoped to that partition by default.
- Default partition column: ``_phlo_partition_date`` (YYYY-MM-DD). Override per check if needed.
- Unpartitioned checks may use a rolling window via ``rolling_window_days``; set ``full_table=True``
  to explicitly run without scoping.

Required metadata keys:
- ``source``: ``pandera``, ``dbt``, or ``phlo``
- ``partition_key``: partition key string (when applicable)
- ``failed_count``: number of failures (schema errors, failed tests, etc.)
- ``total_count``: total evaluated (rows, tests run, etc.) when available
- ``query_or_sql``: SQL/query/command string that produced the evaluation (when applicable)
- ``sample``: <= 20 sample rows/ids/errors (when available)
Optional metadata keys:
- ``repro_sql``: safe SQL snippet for reproducing failures in Trino (e.g. add LIMIT)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from dagster import MetadataValue

PANDERA_CONTRACT_CHECK_NAME = "pandera_contract"


def dbt_check_name(test_type: str, target: str) -> str:
    return f"dbt__{_sanitize_dagster_name(test_type)}__{_sanitize_dagster_name(target)}"


def _sanitize_dagster_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "unknown"


@dataclass(frozen=True, slots=True)
class QualityCheckContract:
    source: Literal["pandera", "dbt", "phlo"]
    failed_count: int
    partition_key: str | None = None
    total_count: int | None = None
    query_or_sql: str | None = None
    repro_sql: str | None = None
    sample: list[Any] | None = None

    def to_dagster_metadata(self) -> dict[str, MetadataValue]:
        metadata: dict[str, MetadataValue] = {
            "source": MetadataValue.text(self.source),
            "failed_count": MetadataValue.int(self.failed_count),
        }

        if self.partition_key is not None:
            metadata["partition_key"] = MetadataValue.text(self.partition_key)

        if self.total_count is not None:
            metadata["total_count"] = MetadataValue.int(self.total_count)

        if self.query_or_sql is not None:
            metadata["query_or_sql"] = MetadataValue.text(self.query_or_sql)

        if self.repro_sql is not None:
            metadata["repro_sql"] = MetadataValue.text(self.repro_sql)

        if self.sample is not None:
            metadata["sample"] = MetadataValue.json(self.sample[:20])

        return metadata
