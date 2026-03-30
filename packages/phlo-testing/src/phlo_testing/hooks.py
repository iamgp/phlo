"""Hook testing utilities for Phlo workflows.

Provides mock implementations and helpers for testing the Phlo hook system,
including event capture, sample event generation, and mock hook bus for
isolated testing.

Example:
    >>> from phlo_testing.hooks import MockHookBus, capture_events, sample_ingestion_event
    >>> bus = MockHookBus()
    >>> captured = capture_events(bus=bus, event_types=["ingestion.end"])
    >>> bus.emit(sample_ingestion_event())
    >>> assert len(captured.events) == 1

"""

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
    """Hook bus that skips plugin discovery for tests.

    A lightweight mock implementation of HookBus that bypasses plugin
    discovery, allowing tests to register and emit events in isolation
    without loading actual plugins.

    Example:
        >>> bus = MockHookBus()
        >>> bus.register(HookRegistration(
        ...     hook_name="test",
        ...     handler=lambda e: print(e),
        ... ))

    """

    def _ensure_discovered(self) -> None:
        """Override discovery to skip plugin loading."""
        self._discovered = True


@dataclass
class CapturedEvents:
    """Capture hook events in memory for assertions.

    A container for collecting hook events emitted during test execution,
    enabling verification of event sequences and properties.

    Attributes:
        events: List of captured HookEvent instances.

    Example:
        >>> captured = CapturedEvents(events=[])
        >>> captured.handler(sample_ingestion_event())
        >>> assert len(captured.events) == 1

    """

    events: list[HookEvent]

    def handler(self, event: HookEvent) -> None:
        """Append a hook event to the captured list.

        Args:
            event: The HookEvent instance to append to the capture list.

        """
        self.events.append(event)


def capture_events(
    *,
    bus: HookBus,
    event_types: Iterable[str] | None = None,
) -> CapturedEvents:
    """Register a hook handler that collects emitted events.

    Creates and registers a capture handler on the provided hook bus,
    optionally filtered to specific event types.

    Args:
        bus: The HookBus instance to register the capture handler on.
        event_types: Optional iterable of event type strings to filter.
            If None, captures all event types.

    Returns:
        A CapturedEvents instance containing the collected events.

    Example:
        >>> bus = MockHookBus()
        >>> captured = capture_events(
        ...     bus=bus,
        ...     event_types=["ingestion.end", "quality.result"]
        ... )
        >>> bus.emit(sample_ingestion_event())
        >>> assert len(captured.events) == 1

    """
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
    """Return a sample ingestion event for tests.

    Creates a pre-configured IngestionEvent representing a successful
    data ingestion operation for testing hook handlers and event processing.

    Returns:
        An IngestionEvent with sample data.

    Example:
        >>> event = sample_ingestion_event()
        >>> assert event.event_type == "ingestion.end"
        >>> assert event.status == "success"

    """
    return IngestionEvent(
        event_type="ingestion.end",
        asset_key="dlt_sample",
        table_name="bronze.sample",
        group_name="sample",
        partition_key="2024-01-01",
        status="success",
    )


def sample_quality_event() -> QualityResultEvent:
    """Return a sample quality check event for tests.

    Creates a pre-configured QualityResultEvent representing a passed
    data quality check for testing hook handlers.

    Returns:
        A QualityResultEvent with sample data.

    Example:
        >>> event = sample_quality_event()
        >>> assert event.event_type == "quality.result"
        >>> assert event.passed is True

    """
    return QualityResultEvent(
        event_type="quality.result",
        asset_key="sample_asset",
        check_name="null_check",
        passed=True,
        check_type="NullCheck",
    )


def sample_transform_event() -> TransformEvent:
    """Return a sample transform event for tests.

    Creates a pre-configured TransformEvent representing a successful
    dbt transformation for testing hook handlers.

    Returns:
        A TransformEvent with sample data.

    Example:
        >>> event = sample_transform_event()
        >>> assert event.event_type == "transform.end"
        >>> assert event.tool == "dbt"

    """
    return TransformEvent(
        event_type="transform.end",
        tool="dbt",
        status="success",
    )


def sample_publish_event() -> PublishEvent:
    """Return a sample publish event for tests.

    Creates a pre-configured PublishEvent representing a successful
    data publication to Postgres for testing hook handlers.

    Returns:
        A PublishEvent with sample data.

    Example:
        >>> event = sample_publish_event()
        >>> assert event.event_type == "publish.end"
        >>> assert event.target_system == "postgres"

    """
    return PublishEvent(
        event_type="publish.end",
        asset_key="publish_sample_marts",
        target_system="postgres",
        tables={"sample": "marts.sample"},
        status="success",
    )


def sample_lineage_event() -> LineageEvent:
    """Return a sample lineage event for tests.

    Creates a pre-configured LineageEvent representing data lineage
    between raw and marts tables for testing hook handlers.

    Returns:
        A LineageEvent with sample data.

    Example:
        >>> event = sample_lineage_event()
        >>> assert event.event_type == "lineage.edges"
        >>> assert ("raw.sample", "marts.sample") in event.edges

    """
    return LineageEvent(
        event_type="lineage.edges",
        edges=[("raw.sample", "marts.sample")],
    )


def sample_telemetry_event() -> TelemetryEvent:
    """Return a sample telemetry event for tests.

    Creates a pre-configured TelemetryEvent representing a metric
    emission for testing hook handlers.

    Returns:
        A TelemetryEvent with sample data.

    Example:
        >>> event = sample_telemetry_event()
        >>> assert event.event_type == "telemetry.metric"
        >>> assert event.name == "sample_metric"

    """
    return TelemetryEvent(
        event_type="telemetry.metric",
        name="sample_metric",
        value=1,
    )


def sample_service_event() -> ServiceLifecycleEvent:
    """Return a sample service lifecycle event for tests.

    Creates a pre-configured ServiceLifecycleEvent representing a service
    startup event for testing hook handlers.

    Returns:
        A ServiceLifecycleEvent with sample data.

    Example:
        >>> event = sample_service_event()
        >>> assert event.event_type == "service.post_start"
        >>> assert event.service_name == "postgres"

    """
    return ServiceLifecycleEvent(
        event_type="service.post_start",
        service_name="postgres",
        phase="post_start",
        status="success",
    )
