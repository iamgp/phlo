"""Sling replication of the PostgreSQL regions lookup for the Delta example.

The compose file in this directory runs PostgreSQL on host port 10732
(user/password/database ``delta``) and ``scripts/seed_postgres.py`` loads the
``public.regions`` lookup.

Platform gap, verified against ``phlo-sling``: its auto-connection resolver
builds only ``PHLO_POSTGRES``, ``PHLO_ICEBERG``, and ``PHLO_S3`` targets.
There is no Delta Lake Sling target, so this stream full-refreshes into a
local Parquet snapshot that the ``delta_regions`` ingestion asset merges into
the Delta table through the provider-neutral table-store interface. When a
``PHLO_DELTA``-style target appears upstream, switching to it is a one-line
change to the override returned below.
"""

from __future__ import annotations

import os
from pathlib import Path

import phlo
from phlo.contracts import SLA, Consumer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_PATH = PROJECT_ROOT / "generated-data" / "regions" / "regions_snapshot.parquet"

DEFAULT_SOURCE_URL = "postgresql://delta:delta@localhost:10732/delta?sslmode=disable"


def source_url() -> str:
    """Return the regions source DSN."""
    return os.environ.get("REGIONS_SOURCE_URL", DEFAULT_SOURCE_URL)


@phlo.ingest.sling(
    stream_name="public.regions",
    table_name="delta_regions_snapshot",
    source_conn=source_url(),
    group="regions",
    mode="full-refresh",
    primary_key="region_code",
    freshness_hours=(168, 192),
    max_runtime_seconds=300,
    max_retries=2,
    retry_delay_seconds=60,
    owner="facilities",
    consumers=[Consumer(name="fleet-reporting", usage="site region enrichment")],
    sla=SLA(freshness_hours=192, quality_threshold=1.0),
)
def replicate_delta_regions_snapshot(context) -> dict[str, str]:
    """Full-refresh the regions lookup into a Parquet hand-off snapshot."""
    del context
    # No tgt_conn on purpose: see module docstring for the platform gap.
    return {"tgt_object": str(SNAPSHOT_PATH)}
