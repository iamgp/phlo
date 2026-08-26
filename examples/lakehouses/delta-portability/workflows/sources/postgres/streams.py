"""Sling replication of the PostgreSQL regions lookup for the Delta example.

The compose file in this directory runs PostgreSQL on host port 10732
(user/password/database ``delta``) and ``scripts/seed_postgres.py`` loads the
``public.regions`` lookup.

The replication full-refreshes into a Parquet hand-off snapshot under
``generated-data/regions/`` that the ``delta_regions`` ingestion asset merges
into the Delta table through the provider-neutral table-store interface.
Re-running is idempotent: full-refresh rewrites the snapshot in place.

The target is an explicit Sling ``file://`` connection rooted at the project:
the ``PHLO_DELTA`` auto-connection shipped in phlo-sling uses the type label
``filesystem``, which Sling 1.5 does not register, so named resolution fails.
"""

from __future__ import annotations

import os
from pathlib import Path

import phlo
from phlo.contracts import SLA, Consumer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_URL = "postgresql://delta:delta@localhost:10732/delta?sslmode=disable"
SNAPSHOT_OBJECT = "generated-data/regions/regions_snapshot.parquet"


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
def replicate_delta_regions_snapshot(context) -> dict[str, object]:
    """Full-refresh the regions lookup into a Parquet hand-off snapshot."""
    del context
    return {"tgt_conn": f"file://{PROJECT_ROOT}", "tgt_object": SNAPSHOT_OBJECT}
