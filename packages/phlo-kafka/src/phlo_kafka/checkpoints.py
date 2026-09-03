"""Checkpoint lifecycle adapter binding Kafka offset ranges to Phlo state.

Resolves the neutral ``IngestionCheckpointStore`` capability (backed by Phlo
Postgres) and derives deterministic idempotency keys from the consumer group,
topic, partition, and start offset, so replaying a committed range resumes
its existing checkpoint instead of claiming a duplicate.
"""

from __future__ import annotations


from phlo.capabilities.interfaces import (
    CheckpointRecord,
    IngestionCheckpointStore,
    SourceOffsetRange,
)
from phlo.capabilities.resolver import resolve_capability
from phlo.exceptions import PhloConfigError


def idempotency_key(*, group_id: str, topic: str, partition: int, start_offset: int) -> str:
    """Return the deterministic claim key for one partition range."""
    return f"{group_id}:{topic}:{partition}:{start_offset}"


def resolve_checkpoint_store(name: str | None = None) -> IngestionCheckpointStore:
    """Resolve the configured checkpoint store capability, failing closed."""
    resolution = resolve_capability("ingestion_checkpoints", name)
    if resolution is None:
        raise PhloConfigError(
            message="Kafka ingestion requires an ingestion checkpoint store capability.",
            suggestions=["Install phlo-postgres to enable durable ingestion checkpoints."],
        )
    return resolution.provider


class KafkaCheckpointAdapter:
    """Drives the claim→staged→committed checkpoint lifecycle for one source."""

    def __init__(
        self,
        *,
        source_id: str,
        group_id: str,
        store: IngestionCheckpointStore | None = None,
    ) -> None:
        self.source_id = source_id
        self.group_id = group_id
        self._store = store

    @property
    def store(self) -> IngestionCheckpointStore:
        if self._store is None:
            self._store = resolve_checkpoint_store()
        return self._store

    def claim_ranges(
        self, *, target_table: str, ranges: list[SourceOffsetRange]
    ) -> CheckpointRecord:
        """Claim consumed ranges; resuming a claimed range is a no-op."""
        first = ranges[0]
        key = idempotency_key(
            group_id=self.group_id,
            topic=first.topic,
            partition=first.partition,
            start_offset=first.start_offset,
        )
        return self.store.claim(
            source_id=self.source_id,
            target_table=target_table,
            ranges=ranges,
            idempotency_key=key,
        )

    def bind_snapshot(
        self, *, checkpoint_id: str, snapshot_id: int | str, release_id: str | None = None
    ) -> CheckpointRecord:
        """Bind the claimed ranges to the staged output snapshot."""
        return self.store.record_snapshot(
            checkpoint_id=checkpoint_id,
            snapshot_id=snapshot_id,
            release_id=release_id,
        )

    def commit(self, *, checkpoint_id: str) -> CheckpointRecord:
        """Commit after the snapshot is audited and promoted."""
        return self.store.commit(checkpoint_id=checkpoint_id)

    def fail(self, *, checkpoint_id: str, reason: str) -> CheckpointRecord:
        """Mark a checkpoint failed; its offsets are retained, not committed."""
        return self.store.fail(checkpoint_id=checkpoint_id, reason=reason)

    def open_checkpoints(self) -> list[CheckpointRecord]:
        """List claimed-but-uncommitted checkpoints needing reconciliation."""
        return self.store.list_open(source_id=self.source_id)
