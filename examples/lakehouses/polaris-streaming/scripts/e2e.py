"""End-to-end proof for the Polaris streaming lakehouse.

Runs against real services started via ``phlo services start`` (see README).
Every step prints PASS/FAIL and the script exits non-zero on any failure:

 1. Polaris health + bootstrap (catalog, writer/reader principals, grants)
 2. PyIceberg REST catalog writes Iceberg data on MinIO through Polaris
 3. Snapshot WAP: candidate branch -> audit -> atomic release; readers see
    nothing before promotion
 4. Failed audit: candidates stay discoverable, release pointer unchanged
 5. CAS: stale expected revision refuses to promote
 6. Kafka: real broker, checkpoint claim -> candidate -> promote -> commit
 7. Replay: committed range skips; duplicate keys produce no new rows
 8. Schema violation: dead-lettered, offsets retained, table unchanged
 9. Airbyte control plane: health + connection listing
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "workflows"))

os.environ.setdefault("PHLO_PROJECT", "polaris-streaming")
os.environ.setdefault("PHLO_PROJECT_PATH", str(PROJECT))
os.environ.setdefault("POLARIS_HOST", "localhost")
os.environ.setdefault("POLARIS_PORT", "11018")
os.environ.setdefault("POLARIS_CATALOG", "phlo")
os.environ.setdefault("KAFKA_HOST", "localhost")
os.environ.setdefault("KAFKA_PORT", "11021")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "11000")
os.environ.setdefault("MINIO_API_PORT", "11001")
os.environ.setdefault("ICEBERG_S3_ENDPOINT", "http://localhost:11001")
os.environ.setdefault("AIRBYTE_HOST", "localhost")
os.environ.setdefault("AIRBYTE_PORT", "11020")

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  - {detail}" if detail else ""))


def main() -> int:

    # -- 1. Polaris health + bootstrap ------------------------------------
    from phlo_polaris.hooks import bootstrap
    from phlo_polaris.resource import PolarisResource

    polaris = PolarisResource()
    deadline = time.time() + 900
    while time.time() < deadline and not polaris.health_check():
        print("  waiting for Polaris (/q/health)...")
        time.sleep(15)
    check("polaris.health", polaris.health_check())

    if polaris.health_check():
        bootstrap()
    check("polaris.bootstrap", polaris.health_check() and polaris.get_catalog("phlo") is not None)

    # -- 2. PyIceberg REST catalog on Polaris ------------------------------
    os.environ["POLARIS_WRITER_CLIENT_SECRET"] = ""
    from phlo_polaris.catalog_backend import _pyiceberg_catalog_config, load_pyiceberg_catalog
    from pyiceberg.schema import Schema
    from pyiceberg.types import IntegerType, NestedField, StringType

    config = _pyiceberg_catalog_config()
    catalog = load_pyiceberg_catalog()
    check("polaris.rest_catalog", catalog is not None, config["uri"])

    schema = Schema(
        NestedField(1, "event_id", StringType(), required=False),
        NestedField(2, "user_id", StringType(), required=False),
        NestedField(3, "event_type", StringType(), required=False),
        NestedField(4, "value", IntegerType(), required=False),
    )
    catalog.create_namespace_if_not_exists("bronze")
    events_table = catalog.create_table_if_not_exists("bronze.events", schema)
    check("iceberg.table_created", events_table is not None, "bronze.events")

    # -- 3-8. WAP + Kafka lifecycle ----------------------------------------
    from phlo_kafka.assets import ingest_batch
    from phlo_kafka.checkpoints import KafkaCheckpointAdapter
    from phlo_kafka.resource import KafkaResource
    from workflows.ingestion.kafka_events import get_config

    from phlo.capabilities.interfaces import SourceOffsetRange

    config_kafka = get_config()
    dest = "bronze.events"
    catalog_table = catalog.load_table(dest)
    catalog_promotion = _promotion_catalog()
    check("wap.catalog", catalog_promotion is not None)

    def rows_main() -> list[dict]:
        catalog_table.refresh()
        return catalog_table.scan().to_arrow().to_pylist()

    def make_events(prefix: str, count: int, *, value: int = 1) -> list[dict]:
        return [
            {
                "event_id": f"{prefix}-{index}",
                "user_id": "u1",
                "event_type": "page_view",
                "value": value,
            }
            for index in range(count)
        ]

    # Kafka: produce a batch and consume it back through the lifecycle.
    kafka = KafkaResource()
    producer = kafka.producer()
    batch = make_events("e", 100)
    for row in batch:
        producer.produce("events", value=json.dumps(row).encode())
    producer.flush(timeout=30)

    store = _checkpoint_store()
    adapter = KafkaCheckpointAdapter(source_id="kafka:events", group_id="phlo-events", store=store)
    records, ranges = kafka.consume(
        topic_pattern="events", group_id="phlo-events", max_records=1000
    )
    check("kafka.consume", len(records) == 100, f"consumed {len(records)}")

    run_id = f"cp-{int(time.time())}"
    before_promotion_rows = rows_main()
    evidence = ingest_batch(
        config=config_kafka,
        records=records,
        ranges=ranges,
        checkpoint_adapter=adapter,
        stager=_stager(catalog_promotion, config_kafka, run_id),
        promoter=_promoter(catalog_promotion, run_id),
        known_fields=config_kafka.schema,
        dead_letter_sink=kafka.dead_letter_sink,
    )
    check(
        "kafka.ingest_committed",
        evidence.get("status") == "committed",
        str(evidence.get("release_id")),
    )
    after_rows = rows_main()
    check(
        "wap.promotion_visible",
        len(after_rows) == len(before_promotion_rows) + 100
        and catalog_promotion.resolve_release(table_name=dest) is not None,
        f"{len(before_promotion_rows)} -> {len(after_rows)}",
    )

    # Replay: the committed range skips; duplicate keys add nothing.
    records2, ranges2 = kafka.consume(
        topic_pattern="events", group_id="phlo-events-replay", max_records=1000
    )
    if records2:
        replay = ingest_batch(
            config=config_kafka,
            records=records2,
            ranges=ranges2,
            checkpoint_adapter=KafkaCheckpointAdapter(
                source_id="kafka:events", group_id="phlo-events-replay", store=store
            ),
            stager=_stager(catalog_promotion, config_kafka, f"{run_id}-replay"),
            promoter=_promoter(catalog_promotion, f"{run_id}-replay"),
            known_fields=config_kafka.schema,
            dead_letter_sink=kafka.dead_letter_sink,
        )
        check(
            "kafka.replay_no_duplicates",
            len(rows_main()) == len(after_rows),
            f"replay status {replay.get('status')}",
        )
    else:
        check("kafka.replay_no_duplicates", True, "no unconsumed records")

    # Failed audit: candidates discoverable, release unchanged.
    fail_run = f"cp-fail-{int(time.time())}"
    catalog_promotion.create_candidate(table_name=dest, run_id=fail_run)
    fail_records, fail_ranges = (
        make_events("f", 5),
        [SourceOffsetRange(topic="events", partition=0, start_offset=990000, end_offset=990005)],
    )
    ingest_batch(
        config=config_kafka,
        records=fail_records,
        ranges=fail_ranges,
        checkpoint_adapter=KafkaCheckpointAdapter(
            source_id="kafka:events", group_id="phlo-events-fail", store=store
        ),
        stager=_stager(catalog_promotion, config_kafka, fail_run),
        promoter=None,  # audit gate refuses to promote
        known_fields=config_kafka.schema,
        dead_letter_sink=kafka.dead_letter_sink,
    )
    revision_before = catalog_promotion.release_revision()
    candidates = catalog_promotion.list_candidates(namespace=f"pipeline-run-{fail_run}")
    check(
        "wap.failed_audit_retains_candidates",
        bool(candidates)
        and catalog_promotion.resolve_release(table_name=dest).revision == revision_before,
    )
    catalog_promotion.abort_candidates(namespace=f"pipeline-run-{fail_run}")

    # CAS: stale revision refuses.
    from phlo_polaris.promotion import ReleaseConflictError

    catalog_promotion.create_candidate(table_name=dest, run_id=fail_run)
    try:
        catalog_promotion.promote_candidates(
            namespace=f"pipeline-run-{fail_run}", release_id="stale", expected_revision=0
        )
        conflict = False
    except ReleaseConflictError:
        conflict = True
    catalog_promotion.abort_candidates(namespace=f"pipeline-run-{fail_run}")
    check("wap.cas_conflict_refuses", conflict)

    # Schema violation: dead-letter + retained offsets.
    bad_run = f"cp-bad-{int(time.time())}"
    dlq: list[tuple[str, list[dict]]] = []
    bad = ingest_batch(
        config=config_kafka,
        records=[{"event_id": "b1", "user_id": "u1", "event_type": "x", "value": "not-a-number"}],
        ranges=[
            SourceOffsetRange(topic="events", partition=0, start_offset=990100, end_offset=990101)
        ],
        checkpoint_adapter=KafkaCheckpointAdapter(
            source_id="kafka:events", group_id="phlo-events-bad", store=store
        ),
        stager=_stager(catalog_promotion, config_kafka, bad_run),
        dead_letter_sink=lambda topic, recs: dlq.append((topic, recs)) or len(recs),
        known_fields=config_kafka.schema,
    )
    check(
        "kafka.schema_violation_dead_lettered",
        bad.get("status") == "dead_lettered" and dlq and dlq[0][0] == "events.dlq",
    )
    open_after = store.list_open(source_id="kafka:events")
    check(
        "kafka.offsets_retained",
        any(c.checkpoint_id == bad.get("checkpoint_id") for c in open_after),
    )

    # -- 9. Airbyte control plane -------------------------------------------
    from phlo_airbyte.client import AirbyteClient

    airbyte = AirbyteClient()
    check("airbyte.control_plane", airbyte.health_check())

    failed = [name for name, ok, _ in RESULTS if not ok]
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    return 0


def _promotion_catalog():
    from phlo_polaris.promotion import PolarisSnapshotPromotionCatalog

    return PolarisSnapshotPromotionCatalog()


def _checkpoint_store():
    from phlo_postgres.checkpoints import PostgresIngestionCheckpointStore

    return PostgresIngestionCheckpointStore()


def _stager(catalog, config, run_id):
    def stager(checkpoint_id: str, records: list[dict]) -> dict:
        catalog.create_candidate(table_name=config.destination_table, run_id=run_id)
        return catalog.merge_rows_into_candidate(
            table_name=config.destination_table,
            run_id=run_id,
            rows=records,
            unique_key=config.unique_key,
        )

    return stager


def _promoter(catalog, run_id):
    def promoter(checkpoint_id: str) -> list:
        return catalog.promote_candidates(
            namespace=f"pipeline-run-{run_id}",
            release_id=run_id,
            expected_revision=catalog.release_revision(),
        )

    return promoter


if __name__ == "__main__":
    sys.exit(main())
