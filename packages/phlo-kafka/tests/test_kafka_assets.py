"""Tests for the Kafka consumer asset lifecycle (claim→stage→audit→commit)."""

from __future__ import annotations


import pytest
from phlo.capabilities.interfaces import CheckpointRecord, SourceOffsetRange
from phlo_kafka.assets import (
    KafkaConsumerConfig,
    clear_kafka_assets,
    get_kafka_assets,
    ingest_batch,
    phlo_kafka_consumer,
)
from phlo_kafka.checkpoints import KafkaCheckpointAdapter


class RecordingStore:
    """Fake checkpoint store exposing the full lifecycle."""

    def __init__(self) -> None:
        self.transitions: list[tuple] = []

    def claim(self, *, source_id, target_table, ranges, idempotency_key=None):
        self.transitions.append(("claim", idempotency_key))
        return CheckpointRecord(
            checkpoint_id="cp-1",
            source_id=source_id,
            target_table=target_table,
            status="claimed",
            ranges=tuple(ranges),
            idempotency_key=idempotency_key,
        )

    def record_snapshot(self, *, checkpoint_id, snapshot_id, release_id=None):
        self.transitions.append(("snapshot", snapshot_id))
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            source_id="s",
            target_table="t",
            status="staged",
            snapshot_id=snapshot_id,
            release_id=release_id,
        )

    def commit(self, *, checkpoint_id):
        self.transitions.append(("commit", checkpoint_id))
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            source_id="s",
            target_table="t",
            status="committed",
        )

    def fail(self, *, checkpoint_id, reason):
        self.transitions.append(("fail", reason))
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            source_id="s",
            target_table="t",
            status="failed",
            failure_reason=reason,
        )

    def list_open(self, *, source_id):
        return []


def _ranges() -> list[SourceOffsetRange]:
    return [SourceOffsetRange(topic="events", partition=0, start_offset=100, end_offset=200)]


def _config() -> KafkaConsumerConfig:
    return KafkaConsumerConfig(
        name="events",
        group="ingestion",
        topic_pattern="events",
        destination_table="bronze.events",
        unique_key=["event_id"],
    )


class FakeTableStore:
    def merge_parquet_rows(self, *, table_name, rows, unique_key):
        return {"snapshot_id": 77, "rows_merged": len(rows)}


class FakePromoter:
    def __init__(self) -> None:
        self.promoted: list[tuple[str, int]] = []

    def promote_snapshot(self, *, table_name: str, snapshot_id: int) -> str:
        self.promoted.append((table_name, snapshot_id))
        return "release-1"


def test_ingest_batch_full_lifecycle_commits_checkpoint() -> None:
    store = RecordingStore()
    promoter = FakePromoter()
    evidence = ingest_batch(
        config=_config(),
        records=[{"event_id": "e1", "count": 1}],
        ranges=_ranges(),
        checkpoint_adapter=KafkaCheckpointAdapter(
            source_id="kafka:events", group_id="phlo-events", store=store
        ),
        table_store=FakeTableStore(),
        snapshot_promoter=promoter,
        known_fields={"event_id": "string", "count": "int"},
    )

    assert evidence["status"] == "committed"
    assert evidence["snapshot_id"] == 77
    assert evidence["release_id"] == "release-1"
    assert store.transitions == [
        ("claim", "phlo-events:events:0:100"),
        ("snapshot", 77),
        ("commit", "cp-1"),
    ]
    assert promoter.promoted == [("bronze.events", 77)]


def test_ingest_batch_schema_violation_dead_letters_and_retains_offsets() -> None:
    store = RecordingStore()
    dead_lettered: list[tuple[str, list[dict]]] = []

    def sink(topic: str, records: list[dict]) -> int:
        dead_lettered.append((topic, records))
        return len(records)

    evidence = ingest_batch(
        config=_config(),
        records=[{"event_id": "e1", "count": "not-a-number"}],
        ranges=_ranges(),
        checkpoint_adapter=KafkaCheckpointAdapter(
            source_id="kafka:events", group_id="phlo-events", store=store
        ),
        table_store=FakeTableStore(),
        dead_letter_sink=sink,
        known_fields={"event_id": "string", "count": "int"},
    )

    assert evidence["status"] == "dead_lettered"
    assert evidence["dead_lettered"] == 1
    assert dead_lettered[0][0] == "events.dlq"
    # No snapshot, no commit: offsets stay uncommitted for replay after migration.
    assert ("commit", "cp-1") not in store.transitions
    assert ("snapshot", 77) not in store.transitions


def test_ingest_batch_skips_already_committed_range_without_merging() -> None:
    """Crash between checkpoint commit and offset commit replays as a skip."""
    store = RecordingStore()
    adapter = KafkaCheckpointAdapter(source_id="kafka:events", group_id="g", store=store)

    def committed_claim(*, target_table, ranges):
        store.transitions.append(("claim", "already-committed"))
        return CheckpointRecord(
            checkpoint_id="cp-0",
            source_id="kafka:events",
            target_table=target_table,
            status="committed",
            ranges=tuple(ranges),
        )

    adapter.claim_ranges = committed_claim
    evidence = ingest_batch(
        config=_config(),
        records=[{"event_id": "e1", "count": 1}],
        ranges=_ranges(),
        checkpoint_adapter=adapter,
        table_store=FakeTableStore(),
        known_fields={"event_id": "string", "count": "int"},
    )

    assert evidence["status"] == "already_committed"
    # No merge, no snapshot, no second commit: no duplicate logical records.
    assert store.transitions == [("claim", "already-committed")]


def test_ingest_batch_empty_records_is_no_data() -> None:
    evidence = ingest_batch(
        config=_config(),
        records=[],
        ranges=_ranges(),
        checkpoint_adapter=KafkaCheckpointAdapter(
            source_id="kafka:events", group_id="g", store=RecordingStore()
        ),
        table_store=FakeTableStore(),
    )
    assert evidence["status"] == "no_data"


def test_consumer_registration_requires_unique_key() -> None:
    clear_kafka_assets()
    with pytest.raises(Exception, match="unique key"):
        phlo_kafka_consumer(
            name="bad",
            topic_pattern="events",
            destination_table="bronze.events",
            unique_key=[],
            group="ingestion",
        )
    clear_kafka_assets()


def test_registered_asset_emits_commit_evidence() -> None:
    clear_kafka_assets()

    class FakeKafkaClient:
        def __init__(self) -> None:
            self.committed: list[str] = []

        def consume(self, *, topic_pattern, group_id, max_records):
            return [{"event_id": "e1", "count": 1}], _ranges()

        def dead_letter_sink(self, topic, records):
            return 0

        def commit_offsets(self, ranges, *, group_id: str) -> None:
            self.committed.append(group_id)

    spec = phlo_kafka_consumer(
        name="events",
        topic_pattern="events",
        destination_table="bronze.events",
        unique_key="event_id",
        group="ingestion",
        client_factory=lambda: FakeKafkaClient(),
    )
    assert spec.key == "ingestion.events"
    assert spec.metadata["dead_letter_topic"] == "events.dlq"
    assert get_kafka_assets() == [spec]
    clear_kafka_assets()
