"""Hook event payload definitions for the Phlo plugin system.

This module defines the dataclass-based event payloads used throughout the
hook system. Each event type inherits from :class:`HookEvent` and adds
specific fields relevant to its lifecycle stage.

Event payloads are immutable dataclasses with correlation tracking for
observability and debugging. All events include:
    - Event type identifier
    - Version for schema evolution
    - UTC timestamp
    - Optional tags for categorization
    - Correlation fields for distributed tracing

Key Event Types:
    - :class:`IngestionEvent`: Data ingestion lifecycle
    - :class:`TransformEvent`: dbt transformation lifecycle
    - :class:`QualityResultEvent`: Data quality check results
    - :class:`ServiceLifecycleEvent`: Service start/stop events
    - :class:`SchemaMigrationEvent`: Schema change tracking
    - :class:`DataMigrationEvent`: Data migration tracking
    - :class:`LineageEvent`: Asset lineage tracking
    - :class:`PublishEvent`: Data publication events
    - :class:`TelemetryEvent`: Metrics and logging events
    - :class:`LogEvent`: Structured log records

Example:
    ```python
    from phlo.hooks.events import IngestionEvent, HookCorrelation
    from datetime import UTC, datetime

    event = IngestionEvent(
        event_type="ingestion.start",
        asset_key="users.raw",
        table_name="users",
        group_name="raw_data",
        correlation=HookCorrelation(
            trace_id="abc-123",
            run_id="run-456"
        )
    )
    ```

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

EVENT_VERSION = "1.0"


def _utc_now() -> datetime:
    """Return the current UTC timestamp.

    Returns:
        datetime: Current time in UTC timezone.

    """
    return datetime.now(UTC)


@dataclass(kw_only=True)
class HookCorrelation:
    """Shared correlation fields for cross-signal observability.

    Correlation fields enable distributed tracing and request tracking across
    multiple events and services. These fields are propagated through the
    event chain to maintain observability context.

    Attributes:
        request_id: Unique identifier for the originating request.
        trace_id: OpenTelemetry trace identifier for distributed tracing.
        span_id: OpenTelemetry span identifier within the trace.
        trace_flags: OpenTelemetry trace flags (sampling decisions).
        run_id: Dagster run identifier for pipeline runs.
        asset_key: Dagster asset key for asset materializations.
        job_name: Dagster job name for pipeline definitions.
        partition_key: Dagster partition key for partitioned runs.
        check_name: Quality check name for quality events.

    Example:
        ```python
        correlation = HookCorrelation(
            trace_id="abc-def-123",
            run_id="run-2024-001",
            asset_key="raw.users"
        )
        ```

    """

    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    trace_flags: str | None = None
    run_id: str | None = None
    asset_key: str | None = None
    job_name: str | None = None
    partition_key: str | None = None
    check_name: str | None = None


@dataclass(kw_only=True)
class HookEvent:
    """Base event payload shared by all hook events.

    This is the foundational event class that all other event types inherit from.
    It provides the common structure for event routing, versioning, and
    correlation tracking.

    Attributes:
        event_type: Event type identifier used for routing (e.g., "ingestion.start").
        version: Event schema version for forward/backward compatibility.
        timestamp: UTC timestamp when the event was created.
        tags: Optional key-value tags for event categorization and filtering.
        correlation: Correlation context for distributed tracing and observability.

    Note:
        All events are immutable dataclasses created with ``kw_only=True`` to
        ensure explicit field naming and prevent positional argument errors.

    Example:
        ```python
        from phlo.hooks.events import HookEvent, HookCorrelation

        event = HookEvent(
            event_type="custom.event",
            tags={"environment": "production"},
            correlation=HookCorrelation(trace_id="abc-123")
        )
        ```

    """

    event_type: str
    version: str = EVENT_VERSION
    timestamp: datetime = field(default_factory=_utc_now)
    tags: dict[str, str] = field(default_factory=dict)
    correlation: HookCorrelation = field(default_factory=HookCorrelation)


@dataclass(kw_only=True)
class ServiceLifecycleEvent(HookEvent):
    """Lifecycle event emitted around service start/stop phases.

    These events track the lifecycle of Phlo-managed services (PostgreSQL,
    MinIO, Trino, etc.) as they are started, stopped, or undergo configuration
    changes.

    Attributes:
        service_name: Name of the service being managed.
        project_name: Name of the project context.
        project_root: Root directory of the project.
        container_name: Docker container name if applicable.
        phase: Lifecycle phase ("start", "stop", "configure", etc.).
        status: Current status of the phase ("started", "completed", "failed").
        metadata: Additional service-specific information.

    Event Types:
        - ``service.start``: Service is starting
        - ``service.stop``: Service is stopping
        - ``service.configure``: Configuration applied

    Example:
        ```python
        from phlo.hooks.events import ServiceLifecycleEvent

        event = ServiceLifecycleEvent(
            event_type="service.start",
            service_name="postgres",
            phase="start",
            status="started",
            metadata={"version": "15.2"}
        )
        ```

    """

    service_name: str
    project_name: str | None = None
    project_root: str | None = None
    container_name: str | None = None
    phase: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class IngestionEvent(HookEvent):
    """Event emitted for data ingestion lifecycle stages.

    These events track the progress of data ingestion operations from sources
    to the lakehouse. They are emitted at the start and end of ingestion runs,
    capturing metrics, status, and any errors that occur.

    Attributes:
        asset_key: Dagster asset key for the ingested table (e.g., "raw.users").
        table_name: Target table name in the lakehouse.
        group_name: Ingestion group classification (e.g., "raw", "staging").
        partition_key: Optional partition identifier for partitioned assets.
        run_id: Unique identifier for this ingestion run.
        branch_name: Git branch name for branch-based ingestion.
        status: Final status of the ingestion ("success", "failed", etc.).
        metrics: Performance metrics (rows_processed, bytes_written, duration).
        error: Error message if ingestion failed.

    Event Types:
        - ``ingestion.start``: Ingestion operation is beginning
        - ``ingestion.end``: Ingestion operation completed
        - ``ingestion.progress``: Periodic progress updates (optional)

    Example:
        ```python
        from phlo.hooks.events import IngestionEvent, HookCorrelation

        # Start event
        start_event = IngestionEvent(
            event_type="ingestion.start",
            asset_key="raw.users",
            table_name="users",
            group_name="raw",
            correlation=HookCorrelation(run_id="run-123")
        )

        # End event with metrics
        end_event = IngestionEvent(
            event_type="ingestion.end",
            asset_key="raw.users",
            table_name="users",
            group_name="raw",
            status="success",
            metrics={"rows_processed": 10000, "duration_seconds": 45.2},
            correlation=HookCorrelation(run_id="run-123")
        )
        ```

    """

    asset_key: str
    table_name: str
    group_name: str
    partition_key: str | None = None
    run_id: str | None = None
    branch_name: str | None = None
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class TransformEvent(HookEvent):
    """Event emitted for dbt transformation lifecycle stages.

    These events track the execution of dbt models and transformations,
    capturing information about which models were run, their status, and
    performance metrics.

    Attributes:
        tool: Transformation tool name (typically "dbt").
        project_dir: Path to the dbt project directory.
        target: dbt target environment (dev, prod, etc.).
        partition_key: Optional partition identifier for partitioned runs.
        asset_key: Dagster asset key if triggered by asset materialization.
        model_names: List of dbt models executed in this run.
        status: Final status ("success", "failed", "error", etc.).
        metrics: Performance metrics (execution_time, rows_affected, etc.).
        error: Error message if transformation failed.

    Event Types:
        - ``transform.start``: Transformation run is beginning
        - ``transform.end``: Transformation run completed

    Example:
        ```python
        from phlo.hooks.events import TransformEvent

        event = TransformEvent(
            event_type="transform.end",
            tool="dbt",
            project_dir="/app/workflows/transforms/dbt",
            target="prod",
            model_names=["stg_users", "dim_users"],
            status="success",
            metrics={"execution_time": 120.5}
        )
        ```

    """

    tool: str
    project_dir: str | None = None
    target: str | None = None
    partition_key: str | None = None
    asset_key: str | None = None
    model_names: list[str] = field(default_factory=list)
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class PublishEvent(HookEvent):
    """Event emitted when publishing data to downstream targets."""

    asset_key: str | None = None
    target_system: str | None = None
    tables: dict[str, str] = field(default_factory=dict)
    status: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass(kw_only=True)
class QualityResultEvent(HookEvent):
    """Event emitted with data quality check outcomes.

    These events report the results of data quality validation checks,
    including pass/fail status, severity level, and metadata about the check.

    Attributes:
        asset_key: Dagster asset key for the checked dataset.
        check_name: Name of the quality check that was executed.
        passed: Boolean indicating if the check passed (True) or failed (False).
        severity: Severity level if check failed ("warning", "error", "critical").
        check_type: Type of quality check ("null", "range", "unique", etc.).
        partition_key: Optional partition identifier for partitioned checks.
        metadata: Additional check-specific results and context.

    Event Types:
        - ``quality.result``: Quality check completed with results

    Example:
        ```python
        from phlo.hooks.events import QualityResultEvent

        # Failed quality check
        event = QualityResultEvent(
            event_type="quality.result",
            asset_key="raw.users",
            check_name="null_check_email",
            passed=False,
            severity="error",
            check_type="null",
            metadata={"failed_rows": 15, "total_rows": 1000}
        )
        ```

    """

    asset_key: str
    check_name: str
    passed: bool
    severity: str | None = None
    check_type: str | None = None
    partition_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class LineageEvent(HookEvent):
    """Event emitted for lineage edges between assets."""

    edges: list[tuple[str, str]] = field(default_factory=list)
    asset_keys: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class TelemetryEvent(HookEvent):
    """Event emitted for telemetry metrics and logs."""

    name: str
    value: Any | None = None
    level: str | None = None
    unit: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class SchemaMigrationEvent(HookEvent):
    """Event emitted for schema migration lifecycle stages."""

    table_name: str
    classification: str
    change_count: int
    status: str
    changes: list[dict[str, Any]] = field(default_factory=list)


@dataclass(kw_only=True)
class DataMigrationEvent(HookEvent):
    """Event emitted for data migration lifecycle stages."""

    migration_name: str
    source_type: str
    destination_table: str
    status: str
    rows_read: int
    rows_written: int
    chunk_index: int | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class LogEvent(HookEvent):
    """Event emitted for structured log records."""

    logger: str
    level: str
    message: str
    service: str | None = None
    run_id: str | None = None
    asset_key: str | None = None
    job_name: str | None = None
    partition_key: str | None = None
    check_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
