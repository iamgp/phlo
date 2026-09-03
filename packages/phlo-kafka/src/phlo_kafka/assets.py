"""Kafka consumer assets: checkpoint-driven effectively-once ingestion.

The lifecycle per consumed batch is:

1. **Claim** the consumed offset ranges in the durable checkpoint store.
2. **Stage** records through an idempotent merge on the declared unique key,
   producing an Iceberg candidate snapshot (at-least-once Kafka, effectively-
   once Iceberg results).
3. **Audit** via schema policy: incompatible schema changes dead-letter the
   batch and retain offsets uncommitted.
4. **Promote**: record the output snapshot on the checkpoint; the
   ``snapshot_promoter`` seam advances a release pointer when a
   snapshot-promotion catalog is wired into the run.
5. **Commit** the checkpoint (and consumer offsets) only after promotion.

Replaying a committed range merges the same keyed rows again, producing no
duplicate logical destination records.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from phlo.capabilities import AssetSpec, MaterializeResult, RunSpec
from phlo.capabilities.interfaces import SourceOffsetRange
from phlo.capabilities.resolver import resolve_capability
from phlo.capabilities.runtime import RuntimeContext
from phlo.exceptions import PhloConfigError
from phlo.logging import get_logger, log_event

from phlo_kafka.checkpoints import KafkaCheckpointAdapter
from phlo_kafka.settings import get_settings

# Populated at decoration time and kept for the process lifetime. Cleared only
# by clear_kafka_assets(), which tests and plugin reloads use to reset state.
_KAFKA_ASSETS: list[AssetSpec] = []


def get_kafka_assets() -> list[AssetSpec]:
    """Return registered Kafka consumer asset specifications."""
    return list(_KAFKA_ASSETS)


def clear_kafka_assets() -> None:
    """Clear all registered Kafka assets (for tests and plugin reloads)."""
    _KAFKA_ASSETS.clear()


@dataclass
class KafkaConsumerConfig:
    """Declaration of one Kafka-consumer-backed destination table."""

    name: str
    group: str
    topic_pattern: str
    destination_table: str
    unique_key: list[str]
    group_id: str | None = None
    schema_policy: str = "additive"
    dead_letter_topic: str | None = None
    max_records_per_batch: int = 10_000
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolved_group_id(self) -> str:
        """Return the consumer group id with the configured prefix."""
        if self.group_id:
            return self.group_id
        return f"{get_settings().kafka_consumer_group_prefix}-{self.name}"

    def resolved_dead_letter_topic(self) -> str:
        """Return the dead-letter topic, deriving one from settings by default."""
        if self.dead_letter_topic:
            return self.dead_letter_topic
        return get_settings().dead_letter_topic(self.topic_pattern)


def _validate_consumer_config(config: KafkaConsumerConfig) -> None:
    if not config.unique_key:
        raise PhloConfigError(
            message=(
                f"Kafka consumer asset {config.name!r} must declare a unique key; "
                "idempotent merges are what make retries produce no duplicates."
            ),
            suggestions=["Declare the record fields that uniquely identify a logical row."],
        )


def ingest_batch(
    *,
    config: KafkaConsumerConfig,
    records: list[dict[str, Any]],
    ranges: list[SourceOffsetRange],
    checkpoint_adapter: KafkaCheckpointAdapter,
    table_store: Any,
    snapshot_promoter: Any | None = None,
    dead_letter_sink: Callable[[str, list[dict[str, Any]]], int] | None = None,
    known_fields: dict[str, str] | None = None,
    logger: Any = None,
) -> dict[str, Any]:
    """Drive one consumed batch through claim→stage→audit→promote→commit.

    On any failure the checkpoint is marked failed and its offsets stay
    uncommitted so the range replays into an idempotent merge.
    """
    logger = logger or get_logger(__name__)
    if not records:
        return {"checkpoint_id": None, "status": "no_data", "rows": 0, "dead_lettered": 0}

    checkpoint = checkpoint_adapter.claim_ranges(
        target_table=config.destination_table, ranges=ranges
    )

    if checkpoint.status == "committed":
        # Replay of an already-committed range (crash between checkpoint
        # commit and offset commit): the ranges are durably represented by
        # their snapshot, so skip instead of merging again.
        log_event(
            logger, "info", "kafka_range_already_committed", checkpoint_id=checkpoint.checkpoint_id
        )
        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "status": "already_committed",
            "rows": 0,
            "dead_lettered": 0,
        }

    # Audit: schema policy. Incompatible changes dead-letter the batch and
    # retain the offsets uncommitted (the checkpoint stays open).
    from phlo_kafka.schema_policy import evaluate_field_types

    decision = evaluate_field_types(existing_schema=known_fields or {}, records=records)
    if decision.decision == "incompatible":
        dead_lettered = 0
        if dead_letter_sink is not None:
            dead_lettered = dead_letter_sink(config.resolved_dead_letter_topic(), records)
        checkpoint_adapter.fail(
            checkpoint_id=checkpoint.checkpoint_id,
            reason=decision.reason or "schema policy",
        )
        log_event(
            logger,
            "warning",
            "kafka_schema_policy_halted",
            reason=decision.reason,
            dead_lettered=dead_lettered,
        )
        return {
            "checkpoint_id": checkpoint.checkpoint_id,
            "status": "dead_lettered",
            "reason": decision.reason,
            "rows": 0,
            "dead_lettered": dead_lettered,
        }

    # Stage: idempotent merge keyed on the declared unique key.
    merge_result = table_store.merge_parquet_rows(
        table_name=config.destination_table,
        rows=records,
        unique_key=config.unique_key,
    )
    snapshot_id = merge_result.get("snapshot_id")

    checkpoint = checkpoint_adapter.bind_snapshot(
        checkpoint_id=checkpoint.checkpoint_id, snapshot_id=snapshot_id
    )

    # Promote: advance the release pointer when a promotion catalog exists.
    release_id = checkpoint.checkpoint_id
    if snapshot_promoter is not None:
        release_id = str(
            snapshot_promoter.promote_snapshot(
                table_name=config.destination_table, snapshot_id=snapshot_id
            )
        )

    checkpoint = checkpoint_adapter.commit(checkpoint_id=checkpoint.checkpoint_id)
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "status": "committed",
        "snapshot_id": snapshot_id,
        "release_id": release_id,
        "rows": merge_result.get("rows_merged", len(records)),
        "dead_lettered": 0,
        "ranges": [
            {
                "topic": item.topic,
                "partition": item.partition,
                "start_offset": item.start_offset,
                "end_offset": item.end_offset,
            }
            for item in ranges
        ],
    }


def _build_asset_run(
    config: KafkaConsumerConfig,
    *,
    client_factory: Callable[[], Any] | None,
) -> Callable[[RuntimeContext], Iterator[MaterializeResult]]:
    """Build the run callable that consumes one batch and lands it safely."""

    def run(runtime: RuntimeContext) -> Iterator[MaterializeResult]:
        logger = runtime.logger
        if client_factory is not None:
            client = client_factory()
        else:
            from phlo_kafka.resource import KafkaResource

            client = KafkaResource()
        records, ranges = client.consume(
            topic_pattern=config.topic_pattern,
            group_id=config.resolved_group_id(),
            max_records=config.max_records_per_batch,
        )
        resolution = resolve_capability("table_store")
        if resolution is None:
            raise PhloConfigError(
                message="Kafka consumer assets require a table store capability.",
                suggestions=["Install phlo-iceberg to write Kafka batches to Iceberg."],
            )
        checkpoint_adapter = KafkaCheckpointAdapter(
            source_id=f"kafka:{config.topic_pattern}",
            group_id=config.resolved_group_id(),
        )
        evidence = ingest_batch(
            config=config,
            records=records,
            ranges=ranges,
            checkpoint_adapter=checkpoint_adapter,
            table_store=resolution.provider,
            dead_letter_sink=(
                client.dead_letter_sink if hasattr(client, "dead_letter_sink") else None
            ),
            logger=logger,
        )
        # Kafka offsets are committed only after the checkpoint committed;
        # a crash before this point replays the range into an idempotent merge.
        if evidence.get("status") == "committed" and hasattr(client, "commit_offsets"):
            client.commit_offsets(ranges, group_id=config.resolved_group_id())
        yield MaterializeResult(
            metadata={
                "kafka_topic": config.topic_pattern,
                "kafka_group": config.resolved_group_id(),
                "destination_table": config.destination_table,
                "checkpoint_id": evidence.get("checkpoint_id"),
                "snapshot_id": evidence.get("snapshot_id"),
                "release_id": evidence.get("release_id"),
                "rows_merged": evidence.get("rows"),
                "dead_lettered": evidence.get("dead_lettered", 0),
                "offset_ranges": evidence.get("ranges", []),
                "status": evidence.get("status"),
            },
            status=(
                "ok"
                if evidence.get("status") in {"committed", "already_committed", "no_data"}
                else "failure"
            ),
        )

    return run


def phlo_kafka_consumer(
    name: str,
    topic_pattern: str,
    destination_table: str,
    unique_key: list[str] | str,
    group: str,
    *,
    group_id: str | None = None,
    schema_policy: str = "additive",
    dead_letter_topic: str | None = None,
    max_records_per_batch: int = 10_000,
    description: str | None = None,
    client_factory: Callable[[], Any] | None = None,
) -> AssetSpec:
    """Register a Kafka consumer asset and return its specification."""
    normalized_key = [unique_key] if isinstance(unique_key, str) else list(unique_key)
    config = KafkaConsumerConfig(
        name=name,
        group=group,
        topic_pattern=topic_pattern,
        destination_table=destination_table,
        unique_key=normalized_key,
        group_id=group_id,
        schema_policy=schema_policy,
        dead_letter_topic=dead_letter_topic,
        max_records_per_batch=max_records_per_batch,
    )
    _validate_consumer_config(config)
    asset_key = f"{group}.{name}"
    spec = AssetSpec(
        key=asset_key,
        group=group,
        description=description
        or f"Consumes Kafka topic {topic_pattern!r} into {destination_table!r}",
        kinds={"kafka", "ingestion"},
        tags={
            "provider": "kafka",
            "asset_type": "ingestion",
            "source": "kafka",
            "schema_policy": schema_policy,
        },
        metadata={
            "provider": "kafka",
            "kafka_topic": topic_pattern,
            "kafka_group": config.resolved_group_id(),
            "destination_table": destination_table,
            "unique_key": normalized_key,
            "schema_policy": schema_policy,
            "dead_letter_topic": config.resolved_dead_letter_topic(),
            "group": group,
        },
        partitions=None,
        resources=set(),
        run=RunSpec(
            fn=_build_asset_run(config, client_factory=client_factory),
            max_runtime_seconds=3600,
            max_retries=1,
            retry_delay_seconds=30,
            cron=None,
            freshness_hours=None,
        ),
        checks=[],
    )
    _KAFKA_ASSETS.append(spec)
    return spec
