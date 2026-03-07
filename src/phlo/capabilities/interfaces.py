"""Runtime capability interfaces used by capability providers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TableStore(Protocol):
    """Protocol for table-store providers used by ingestion components.

    Required methods: ``ensure_table``, ``append_parquet``, ``merge_parquet``.
    Extended operations (``overwrite_parquet``, ``delete_rows``, ``compact``,
    ``list_snapshots``, ``rollback_to_snapshot``, ``vacuum``) raise
    ``NotImplementedError`` by default so providers opt in incrementally.
    """

    def ensure_table(
        self,
        *,
        table_name: str,
        schema: Any,
        partition_spec: Any = None,
        override_ref: str | None = None,
    ) -> Any:
        """Ensure a destination table exists."""

    def append_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Append staged parquet data to a destination table."""

    def merge_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        unique_key: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Merge staged parquet data into a destination table."""

    def overwrite_parquet(
        self,
        *,
        table_name: str,
        data_path: str | Path,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Overwrite a table with staged parquet data."""
        raise NotImplementedError

    def delete_rows(
        self,
        *,
        table_name: str,
        predicate: str,
        override_ref: str | None = None,
    ) -> dict[str, int]:
        """Delete rows matching a predicate expression."""
        raise NotImplementedError

    def compact(
        self,
        *,
        table_name: str,
        override_ref: str | None = None,
    ) -> dict[str, Any]:
        """Compact small files in a table."""
        raise NotImplementedError

    def list_snapshots(
        self,
        *,
        table_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List recent table snapshots for time-travel queries."""
        raise NotImplementedError

    def rollback_to_snapshot(
        self,
        *,
        table_name: str,
        snapshot_id: int | str,
    ) -> dict[str, Any]:
        """Roll back a table to a previous snapshot."""
        raise NotImplementedError

    def vacuum(
        self,
        *,
        table_name: str,
        retain_hours: int = 168,
    ) -> dict[str, Any]:
        """Remove orphan files older than the retention period."""
        raise NotImplementedError


@runtime_checkable
class VersionedCatalog(Protocol):
    """Protocol for optional catalog/versioning providers.

    Providers opt in when they support explicit branch lifecycle management
    for versioned analytical storage.
    """

    def list_branches(self) -> list[Any]:
        """List known branch references."""
        ...

    def get_branch_hash(self, name: str) -> str | None:
        """Resolve the current hash for a branch."""
        ...

    def create_branch(self, name: str, from_ref: str = "main") -> str | None:
        """Create a new branch from an existing reference."""
        ...

    def merge_branch(self, source: str, target: str = "main") -> bool:
        """Merge a source branch into a target branch."""
        ...

    def delete_branch(self, name: str) -> bool:
        """Delete a branch reference."""
        ...


@runtime_checkable
class CatalogScanner(Protocol):
    """Protocol for catalog scanners used by metadata synchronization flows."""

    def scan_all_tables(self) -> dict[str, list[dict[str, Any]]]:
        """Return all discovered tables grouped by namespace."""
        ...

    def get_table_metadata(self, namespace: str, table_name: str) -> dict[str, Any] | None:
        """Return normalized metadata for one discovered table."""
        ...


@runtime_checkable
class GovernanceBackend(Protocol):
    """Protocol for governance providers (access control, masking, policies)."""

    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List access policies, optionally filtered by table."""
        ...

    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply an access policy to the backend."""
        ...

    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke an access policy by identifier."""
        ...

    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check whether a principal has access for an action on a table."""
        ...


@runtime_checkable
class SecretBackend(Protocol):
    """Protocol for pluggable secret storage providers."""

    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret value by key."""
        ...

    def list_secrets(self) -> list[str]:
        """List available secret keys."""
        ...


@runtime_checkable
class SchemaExtractor(Protocol):
    """Protocol for extracting a NormalizedSchema from a quality provider's native schema."""

    def extract(self, native_schema: Any) -> Any:
        """Convert a native schema into a NormalizedSchema."""
        ...


@runtime_checkable
class MetadataCatalog(Protocol):
    """Protocol for metadata catalog providers."""

    def health_check(self) -> bool:
        """Check provider connectivity and readiness."""
        ...

    def upsert_table(self, *, namespace: str, table: Any) -> Any:
        """Create or update one table definition in the metadata catalog."""
        ...

    def publish_quality_result(self, *, event: Any) -> None:
        """Publish one quality result payload to the metadata catalog."""
        ...

    def publish_lineage_edges(self, *, edges: list[tuple[str, str]]) -> None:
        """Publish directed lineage edges to the metadata catalog."""
        ...


@runtime_checkable
class QueryEngine(Protocol):
    """Protocol for SQL query engines used by maintenance and discovery flows."""

    def execute(
        self,
        sql: str,
        params: Any = None,
        schema: str | None = None,
    ) -> Any:
        """Execute SQL and return provider-native results."""
        ...


@runtime_checkable
class LineageSink(Protocol):
    """Protocol for lineage backends and queryable lineage stores."""

    def record_asset_edges(
        self,
        edges: list[tuple[str, str]],
        *,
        asset_keys: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> int:
        """Persist directed asset lineage edges."""
        ...

    def record_row_lineage(
        self,
        *,
        row_id: str,
        table_name: str,
        source_type: str,
        parent_row_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist one row-level lineage record."""
        ...

    def get_asset_graph(self) -> Any:
        """Return the current asset-level lineage graph representation."""
        ...

    def get_row_journey(self, *, row_id: str, depth: int = 10) -> Any:
        """Return upstream and downstream lineage for one row identifier."""
        ...


@runtime_checkable
class MaintenanceReadModel(Protocol):
    """Protocol for maintenance and observability status read models."""

    def load_maintenance_status(self) -> Any:
        """Load the current maintenance status snapshot."""
        ...

    def render_maintenance_prometheus(self) -> str:
        """Render maintenance metrics in Prometheus text format."""
        ...


@runtime_checkable
class AlertSink(Protocol):
    """Protocol for alerting providers used by orchestrators and APIs."""

    def send_alert(
        self,
        *,
        title: str,
        message: str,
        severity: str | None = None,
        asset_name: str | None = None,
        run_id: str | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Send one alert notification."""
        ...


@runtime_checkable
class ApiBackend(Protocol):
    """Protocol for swappable API and graph-serving backends."""

    def health_check(self) -> bool:
        """Check backend connectivity and readiness."""
        ...

    def describe(self) -> dict[str, Any]:
        """Return backend metadata and public endpoint information."""
        ...


@runtime_checkable
class SchemaMigrator(Protocol):
    """Protocol for storage-layer schema migration providers.

    Each storage provider (Iceberg, Delta, Hudi) implements this protocol
    and determines its own classification rules based on its capabilities.
    """

    def supported_changes(self) -> set[str]:
        """Return the set of change_type values this provider supports natively."""
        ...

    def classify_change(self, change_type: str, **details: Any) -> str:
        """Classify a single change as 'safe', 'warning', or 'breaking'."""
        ...

    def diff_schema(self, *, table_name: str, desired: Any) -> Any:
        """Compare desired schema against current table and produce a migration plan."""
        ...

    def apply_plan(self, *, plan: Any, approved: bool = False) -> dict[str, Any]:
        """Execute a migration plan. Breaking changes require approved=True."""
        ...

    def get_schema_history(self, *, table_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return schema version history for a table."""
        ...


class AccessPolicy:
    """Value object describing an access control policy."""

    __slots__ = (
        "policy_id",
        "principal",
        "table_pattern",
        "action",
        "effect",
        "columns",
        "row_filter",
        "data_masking",
    )

    def __init__(
        self,
        *,
        policy_id: str | None = None,
        principal: str,
        table_pattern: str,
        action: str = "SELECT",
        effect: str = "ALLOW",
        columns: list[str] | None = None,
        row_filter: str | None = None,
        data_masking: dict[str, str] | None = None,
    ) -> None:
        self.policy_id = policy_id
        self.principal = principal
        self.table_pattern = table_pattern
        self.action = action
        self.effect = effect
        self.columns = columns
        self.row_filter = row_filter
        self.data_masking = data_masking


@dataclass(frozen=True)
class PlatformHealthSummary:
    """Platform health summary from observability backend."""

    overall_status: str
    components: dict[str, str]
    timestamp: str


@dataclass(frozen=True)
class ServiceStatus:
    """Service status from observability backend."""

    name: str
    status: str
    last_check: str


@dataclass(frozen=True)
class PlatformMetricsSummary:
    """Platform metrics summary from observability backend."""

    period: str
    metrics: dict[str, Any]
    timestamp: str


@dataclass(frozen=True)
class AlertSummary:
    """Alert summary from observability backend."""

    title: str
    severity: str
    status: str
    fired_at: str


@dataclass(frozen=True)
class DashboardLink:
    """Dashboard link from observability backend."""

    title: str
    url: str
    category: str | None = None


@runtime_checkable
class ObservabilityBackend(Protocol):
    """Protocol for swappable observability backends (metrics, logs, dashboards)."""

    def health_summary(self) -> PlatformHealthSummary:
        """Return platform health summary."""
        ...

    def service_status(self) -> list[ServiceStatus]:
        """Return service status list."""
        ...

    def platform_metrics(self, period: str) -> PlatformMetricsSummary:
        """Return platform metrics for the specified period."""
        ...

    def recent_alerts(self, limit: int) -> list[AlertSummary]:
        """Return recent alerts up to the specified limit."""
        ...

    def dashboard_links(self) -> list[DashboardLink]:
        """Return available dashboard links."""
        ...

    def logs_query_link(self, service: str | None = None) -> str | None:
        """Return a link to query logs, optionally filtered by service."""
        ...

    def metrics_query_link(self, metric: str | None = None) -> str | None:
        """Return a link to query metrics, optionally filtered by metric."""
        ...
