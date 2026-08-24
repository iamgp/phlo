"""DLT merge of the Sling regions snapshot into the Delta table.

The snapshot produced (or replayed) by the Sling stream is merged by
``region_code`` into ``raw.delta_regions``. Re-running the full refresh is
idempotent: the merge upserts every row and never grows the table.
"""

from __future__ import annotations

from pathlib import Path

import dlt
import pandas as pd
import phlo
from phlo.contracts import SLA, Consumer

from workflows.schemas.telemetry import RegionDirectorySchema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "generated-data" / "regions" / "regions_snapshot.parquet"
REPLAY_PATH = PROJECT_ROOT / "generated-data" / "regions" / "regions.csv"
DELTA_ROUTING = {"table_store": "delta"}


def read_region_snapshot(snapshot_path: Path = SNAPSHOT_PATH) -> pd.DataFrame:
    """Read the replicated snapshot, falling back to the CSV replay fixture.

    The Parquet snapshot only exists after a live Sling run against the
    compose PostgreSQL source; without it, the deterministic ``regions.csv``
    fixture replays the same rows offline.
    """
    if snapshot_path.exists():
        return pd.read_parquet(snapshot_path)
    fallback = snapshot_path.with_name("regions.csv")
    frame = pd.read_csv(fallback)
    frame["updated_at"] = pd.to_datetime(frame["updated_at"])
    return frame


@phlo.ingest.dlt(
    table_name="delta_regions",
    unique_key="region_code",
    validation_schema=RegionDirectorySchema,
    group="regions",
    capabilities=DELTA_ROUTING,
    partitioned=False,
    freshness_hours=(168, 192),
    merge_strategy="merge",
    strict_validation=True,
    max_runtime_seconds=120,
    max_retries=2,
    retry_delay_seconds=60,
    add_metadata_columns=True,
    owner="facilities",
    consumers=[Consumer(name="fleet-reporting", usage="site region enrichment")],
    sla=SLA(freshness_hours=192, quality_threshold=1.0),
)
def delta_regions(partition_date: str) -> object:
    """Merge the replicated regions lookup into Delta."""
    del partition_date
    return dlt.resource(
        read_region_snapshot().to_dict("records"),
        name="delta_regions",
    )
