"""Provider-neutral Observatory v2 API models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

HealthState = Literal["ok", "warning", "error", "unknown"]
ServiceStatus = Literal["running", "stopped", "unhealthy", "starting", "unknown"]
ServiceDefinitionState = Literal["configured", "available"]
OperationStatus = Literal["queued", "running", "succeeded", "failed", "skipped", "unknown"]
RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled", "unknown"]
QualityStatus = Literal["passing", "failing", "warning", "unknown"]


class V2Health(BaseModel):
    """Neutral health state for any v2 resource."""

    state: HealthState
    message: str | None = None


class V2ExternalLink(BaseModel):
    """Provider-neutral link exposed to Observatory."""

    label: str
    url: str
    kind: str = "external"


class V2CapabilityPage(BaseModel):
    """Provider-neutral Observatory page availability."""

    id: str
    label: str
    path: str
    available: bool
    nav: bool = True
    reason: str | None = None
    providers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2Capabilities(BaseModel):
    """Provider-neutral Observatory surface capability contract."""

    version: int = 2
    pages: list[V2CapabilityPage] = Field(default_factory=list)
    features: dict[str, bool] = Field(default_factory=dict)
    providers: dict[str, list[str]] = Field(default_factory=dict)


class V2CapabilitySupport(BaseModel):
    """Provider support flags exposed to Observatory."""

    supports_refs: bool = False
    supports_snapshots: bool = False
    supports_schema_evolution: bool = False
    supports_atomic_validation: bool = False
    supports_promote: bool = False
    supports_time_travel: bool = False
    supports_metrics: bool = False
    supports_logs: bool = False
    supports_dashboards: bool = False
    supports_alerts: bool = False
    supports_permissions: bool = False
    supports_attributes: bool = False


class V2CapabilityProvider(BaseModel):
    """One installed provider for a Phlo capability type."""

    capability_type: str
    name: str
    display_name: str
    package: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    support: V2CapabilitySupport = Field(default_factory=V2CapabilitySupport)
    health: V2Health = Field(default_factory=lambda: V2Health(state="unknown"))
    native_links: list[V2ExternalLink] = Field(default_factory=list)


class V2UiContribution(BaseModel):
    """Provider-neutral UI contribution exposed by a Phlo capability."""

    name: str
    capability_type: str
    capability_name: str
    surfaces: list[str]
    read_models: dict[str, str]
    actions: list[str]
    native_links: list[V2ExternalLink] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2RouteRequirement(BaseModel):
    """Capability requirements for one Observatory route."""

    route_id: str
    label: str
    path: str
    required_any: list[str] = Field(default_factory=list)
    required_all: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    nav: bool = True
    reason: str = ""


class V2CapabilityInventory(BaseModel):
    """Full capability inventory used to drive Observatory navigation."""

    version: int = 2
    providers: dict[str, list[V2CapabilityProvider]] = Field(default_factory=dict)
    requirements: list[V2RouteRequirement] = Field(default_factory=list)
    ui_contributions: list[V2UiContribution] = Field(default_factory=list)


class V2ResourceRef(BaseModel):
    """Small reference to another Observatory v2 resource."""

    kind: str
    id: str
    label: str


class V2SurfaceItem(BaseModel):
    """Provider-neutral top-level surface summary."""

    id: str
    name: str
    kind: str
    health: V2Health = Field(default_factory=lambda: V2Health(state="unknown"))
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2Action(BaseModel):
    """Provider-neutral action descriptor."""

    id: str
    label: str
    kind: str
    enabled: bool = False
    requires_confirmation: bool = True
    reason: str | None = None
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    required_capability: str | None = None
    required_service: str | None = None
    required_permission: str | None = None
    equivalent_cli_command: str | None = None
    expected_evidence: list[str] = Field(default_factory=list)
    background_operation_id: str | None = None


class V2ActionRequest(BaseModel):
    """Request to execute a guarded Observatory action."""

    action_id: str


class V2ActionResult(BaseModel):
    """Provider-neutral result of a guarded Observatory action."""

    action: V2Action
    status: Literal["succeeded", "failed", "skipped"]
    message: str
    operation: "V2Operation | None" = None


class V2PackageInstallRequest(BaseModel):
    """Request to install a Phlo package from the trusted registry."""

    package_name: str


class V2PackageInstallResult(BaseModel):
    """Result of a Python package install requested by Observatory."""

    package_name: str
    package_spec: str
    status: Literal["succeeded", "failed", "skipped"]
    message: str
    services: list[str] = Field(default_factory=list)


class V2ServicePort(BaseModel):
    """Provider-neutral service port exposure."""

    name: str
    target: str
    published: str | None = None


class V2ServiceConfigEntry(BaseModel):
    """Non-secret service configuration hint."""

    name: str
    value: str | None = None
    description: str | None = None
    secret: bool = False


class V2Service(BaseModel):
    """Provider-neutral service summary."""

    id: str
    name: str
    kind: str
    status: ServiceStatus
    health: V2Health
    definition_state: ServiceDefinitionState = "available"
    runtime_state: ServiceStatus = "unknown"
    in_stack: bool = False
    disabled: bool = False
    profile: str | None = None
    backend: str = "unknown"
    depends_on: list[str] = Field(default_factory=list)
    impacts: list[str] = Field(default_factory=list)
    links: list[V2ExternalLink] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2ServiceDetail(BaseModel):
    """Provider-neutral service detail."""

    service: V2Service
    dependencies: list[V2Service] = Field(default_factory=list)
    dependents: list[V2Service] = Field(default_factory=list)
    actions: list[V2Action] = Field(default_factory=list)
    logs: list["V2LogEvent"] = Field(default_factory=list)
    ports: list[V2ServicePort] = Field(default_factory=list)
    config: list[V2ServiceConfigEntry] = Field(default_factory=list)


class V2Overview(BaseModel):
    """First slice of the Observatory v2 overview payload."""

    health: V2Health
    counters: dict[str, int] = Field(default_factory=dict)
    recent: list[V2ResourceRef] = Field(default_factory=list)


class V2Operation(BaseModel):
    """Provider-neutral operation summary."""

    id: str
    name: str
    kind: str
    status: OperationStatus
    health: V2Health
    target: V2ResourceRef | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2OperationDetail(BaseModel):
    """Provider-neutral operation detail."""

    operation: V2Operation
    related: list[V2ResourceRef] = Field(default_factory=list)
    logs: list["V2LogEvent"] = Field(default_factory=list)
    actions: list[V2Action] = Field(default_factory=list)


class V2Run(BaseModel):
    """Provider-neutral orchestrator run summary."""

    id: str
    name: str
    status: RunStatus = "unknown"
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    assets: list[V2ResourceRef] = Field(default_factory=list)
    checks: list[V2ResourceRef] = Field(default_factory=list)
    logs: list[V2ResourceRef] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2Asset(BaseModel):
    """Provider-neutral asset summary."""

    id: str
    name: str
    group: str | None = None
    description: str | None = None
    kinds: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2AssetDetail(BaseModel):
    """Provider-neutral asset detail with related operational context."""

    asset: V2Asset
    upstream: list[V2Asset] = Field(default_factory=list)
    downstream: list[V2Asset] = Field(default_factory=list)
    tables: list["V2Table"] = Field(default_factory=list)
    quality: list["V2QualityCheck"] = Field(default_factory=list)
    logs: list["V2LogEvent"] = Field(default_factory=list)
    operations: list["V2Operation"] = Field(default_factory=list)
    lineage: list[V2ResourceRef] = Field(default_factory=list)
    materializations: list["V2Operation"] = Field(default_factory=list)
    column_lineage: dict[str, list[str]] = Field(default_factory=dict)


class V2AssetGraphNode(BaseModel):
    """Provider-neutral asset graph node."""

    id: str
    key: list[str] = Field(default_factory=list)
    key_path: str
    label: str
    description: str | None = None
    compute_kind: str | None = None
    group_name: str | None = None
    layer: str = "unknown"
    last_materialization: str | None = None
    upstream_count: int = 0
    downstream_count: int = 0


class V2AssetGraphEdge(BaseModel):
    """Provider-neutral asset graph edge."""

    source: str
    target: str


class V2AssetGraph(BaseModel):
    """Provider-neutral asset graph."""

    nodes: list[V2AssetGraphNode] = Field(default_factory=list)
    edges: list[V2AssetGraphEdge] = Field(default_factory=list)


class V2ImpactedAsset(BaseModel):
    """Provider-neutral downstream impact summary."""

    key_path: str
    label: str
    layer: str = "unknown"
    depth: int


class V2Table(BaseModel):
    """Provider-neutral table summary."""

    id: str
    name: str
    namespace: str | None = None
    asset_id: str | None = None
    format: str | None = None
    branch: str | None = None
    schema_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2TablePreview(BaseModel):
    """Provider-neutral table preview metadata.

    Rows are optional because phlo-api v2 must not couple Observatory to a
    specific query engine. Implementations can populate rows when a core
    provider-neutral query contract exists.
    """

    table: V2Table
    columns: list[str] = Field(default_factory=list)
    column_types: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    limit: int = 50
    offset: int = 0
    has_more: bool = False


class V2QueryRequest(BaseModel):
    """Provider-neutral read query request."""

    sql: str
    branch: str | None = None
    limit: int = 100
    offset: int = 0


class V2QueryResult(BaseModel):
    """Provider-neutral read query result."""

    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    effective_sql: str
    limit: int
    offset: int = 0
    warnings: list[str] = Field(default_factory=list)


class V2SavedQuery(BaseModel):
    """Persisted Observatory query."""

    id: str
    name: str
    sql: str
    branch: str | None = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2SavedQueryRequest(BaseModel):
    """Create or update a saved query."""

    name: str
    sql: str
    branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2StageDiff(BaseModel):
    """Provider-neutral table stage diff."""

    source: "V2Table"
    target: "V2Table"
    columns: dict[str, list[str]] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2RowJourney(BaseModel):
    """Provider-neutral row journey and provenance context."""

    table: "V2Table"
    row_id: str
    row: dict[str, Any] = Field(default_factory=dict)
    upstream: list[V2ResourceRef] = Field(default_factory=list)
    downstream: list[V2ResourceRef] = Field(default_factory=list)
    stages: list[V2ResourceRef] = Field(default_factory=list)
    logs: list["V2LogEvent"] = Field(default_factory=list)
    diff: dict[str, Any] = Field(default_factory=dict)


class V2UpstreamTableRef(BaseModel):
    """Resolved upstream table identifier for row provenance."""

    model_config = {"populate_by_name": True}

    schema_name: str = Field(alias="schema")
    table: str


class V2ContributingRowsQueryRequest(BaseModel):
    """Request for a contributing-rows query."""

    downstream_asset_key: str
    upstream_asset_key: str
    row_data: dict[str, Any]
    limit: int | None = None
    trino_url: str | None = None
    timeout_ms: int | None = None
    catalog: str | None = None


class V2ContributingRowsQueryResponse(BaseModel):
    """Generated contributing-rows query."""

    query: str
    upstream: V2UpstreamTableRef


class V2ContributingRowsPageRequest(BaseModel):
    """Request for a page of contributing rows."""

    downstream_asset_key: str
    upstream_asset_key: str
    row_data: dict[str, Any]
    page: int | None = None
    page_size: int | None = None
    trino_url: str | None = None
    timeout_ms: int | None = None
    catalog: str | None = None


class V2ContributingRowsPageResponse(BaseModel):
    """Page of contributing rows."""

    mode: Literal["entity", "aggregate"]
    page: int
    page_size: int
    has_more: bool
    query: str
    upstream: V2UpstreamTableRef
    columns: list[str] = Field(default_factory=list)
    column_types: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class V2QualityCheck(BaseModel):
    """Provider-neutral quality check summary."""

    id: str
    name: str
    asset_id: str
    status: QualityStatus
    severity: str | None = None
    blocking: bool = True
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2QualityDetail(BaseModel):
    """Provider-neutral quality check detail."""

    check: V2QualityCheck
    asset: V2Asset | None = None
    history: list[V2Operation] = Field(default_factory=list)
    logs: list[V2LogEvent] = Field(default_factory=list)
    actions: list[V2Action] = Field(default_factory=list)


class V2LogEvent(BaseModel):
    """Provider-neutral log event summary."""

    id: str
    timestamp: str | None = None
    level: str = "info"
    message: str
    source: str | None = None
    resource: V2ResourceRef | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2LogFacets(BaseModel):
    """Provider-neutral log filter facets."""

    sources: list[str] = Field(default_factory=list)
    levels: list[str] = Field(default_factory=list)
    resources: list[V2ResourceRef] = Field(default_factory=list)


class V2Branch(BaseModel):
    """Provider-neutral data branch summary."""

    id: str
    name: str
    current: bool = False
    protected: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2BranchDetail(BaseModel):
    """Provider-neutral branch detail."""

    branch: V2Branch
    contents: list[V2ResourceRef] = Field(default_factory=list)
    commits: list[V2Operation] = Field(default_factory=list)
    compare: dict[str, int] = Field(default_factory=dict)
    tables: list["V2Table"] = Field(default_factory=list)


class V2Extension(BaseModel):
    """Provider-neutral Observatory extension summary."""

    id: str
    name: str
    version: str | None = None
    enabled: bool = True
    routes: list[str] = Field(default_factory=list)
    nav: list[str] = Field(default_factory=list)
    settings_scope: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2ExtensionDetail(BaseModel):
    """Provider-neutral extension detail."""

    extension: V2Extension
    routes: list[str] = Field(default_factory=list)
    nav: list[str] = Field(default_factory=list)
    capabilities: list[V2ResourceRef] = Field(default_factory=list)


class V2Settings(BaseModel):
    """Provider-neutral Observatory v2 settings summary."""

    version: int = 2
    defaults: dict[str, str] = Field(default_factory=dict)
    features: dict[str, bool] = Field(default_factory=dict)
    storage: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2SearchResult(BaseModel):
    """Provider-neutral Observatory search result."""

    id: str
    label: str
    kind: str
    summary: str | None = None
    href: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class V2ServiceList(BaseModel):
    """List envelope for v2 services."""

    items: list[V2Service]


class V2OperationList(BaseModel):
    """List envelope for v2 operations."""

    items: list[V2Operation]


class V2RunList(BaseModel):
    """List envelope for v2 orchestrator runs."""

    items: list[V2Run]
    next_cursor: str | None = None


class V2AssetList(BaseModel):
    """List envelope for v2 assets."""

    items: list[V2Asset]
    next_cursor: str | None = None


class V2TableList(BaseModel):
    """List envelope for v2 tables."""

    items: list[V2Table]


class V2QualityList(BaseModel):
    """List envelope for v2 quality checks."""

    items: list[V2QualityCheck]


class V2LogList(BaseModel):
    """List envelope for v2 log events."""

    items: list[V2LogEvent]


class V2BranchList(BaseModel):
    """List envelope for v2 branches."""

    items: list[V2Branch]


class V2ExtensionList(BaseModel):
    """List envelope for v2 extensions."""

    items: list[V2Extension]


class V2SearchList(BaseModel):
    """List envelope for v2 search results."""

    items: list[V2SearchResult]
    next_cursor: str | None = None


class V2SavedQueryList(BaseModel):
    """List envelope for saved Observatory queries."""

    items: list[V2SavedQuery]


class V2SurfaceList(BaseModel):
    """List envelope for provider-neutral top-level surfaces."""

    items: list[V2SurfaceItem]
