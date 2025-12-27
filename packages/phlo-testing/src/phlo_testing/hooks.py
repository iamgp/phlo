"""Hook testing utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from phlo.hooks import (
    HookEvent,
    IngestionEvent,
    LineageEvent,
    PublishEvent,
    QualityResultEvent,
    ServiceLifecycleEvent,
    TelemetryEvent,
    TransformEvent,
)
from phlo.hooks.bus import HookBus
from phlo.plugins.hooks import HookFilter, HookRegistration


class MockHookBus(HookBus):
    """Hook bus that skips plugin discovery for tests."""

    def _ensure_discovered(self) -> None:
        self._discovered = True


@dataclass
class CapturedEvents:
    """Capture hook events in memory for assertions."""

    events: list[HookEvent]

    def handler(self, event: HookEvent) -> None:
        """Append a hook event to the captured list."""

        self.events.append(event)


def capture_events(
    *,
    bus: HookBus,
    event_types: Iterable[str] | None = None,
) -> CapturedEvents:
    """Register a hook handler that collects emitted events."""

    captured = CapturedEvents(events=[])
    filters = HookFilter(event_types=set(event_types)) if event_types else None
    bus.register(
        HookRegistration(
            hook_name="capture_events",
            handler=captured.handler,
            filters=filters,
        ),
        plugin_name="phlo-testing",
    )
    return captured


def sample_ingestion_event() -> IngestionEvent:
    """Return a sample ingestion event for tests."""

    return IngestionEvent(
        event_type="ingestion.end",
        asset_key="dlt_sample",
        table_name="bronze.sample",
        group_name="sample",
        partition_key="2024-01-01",
        status="success",
    )


def sample_quality_event() -> QualityResultEvent:
    """Return a sample quality event for tests."""

    return QualityResultEvent(
        event_type="quality.result",
        asset_key="sample_asset",
        check_name="null_check",
        passed=True,
        check_type="NullCheck",
    )


def sample_transform_event() -> TransformEvent:
    """Return a sample transform event for tests."""

    return TransformEvent(
        event_type="transform.end",
        tool="dbt",
        status="success",
    )


def sample_publish_event() -> PublishEvent:
    """Return a sample publish event for tests."""

    return PublishEvent(
        event_type="publish.end",
        asset_key="publish_sample_marts",
        target_system="postgres",
        tables={"sample": "marts.sample"},
        status="success",
    )


def sample_lineage_event() -> LineageEvent:
    """Return a sample lineage event for tests."""

    return LineageEvent(
        event_type="lineage.edges",
        edges=[("raw.sample", "marts.sample")],
    )


def sample_telemetry_event() -> TelemetryEvent:
    """Return a sample telemetry event for tests."""

    return TelemetryEvent(
        event_type="telemetry.metric",
        name="sample_metric",
        value=1,
    )


def sample_service_event() -> ServiceLifecycleEvent:
    """Return a sample service lifecycle event for tests."""

    return ServiceLifecycleEvent(
        event_type="service.post_start",
        service_name="postgres",
        phase="post_start",
        status="success",
    )
