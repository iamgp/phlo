"""Provider-neutral Observatory v2 API models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

HealthState = Literal["ok", "warning", "error", "unknown"]
ServiceStatus = Literal["running", "stopped", "unhealthy", "starting", "unknown"]
OperationStatus = Literal["queued", "running", "succeeded", "failed", "unknown"]
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


class V2ResourceRef(BaseModel):
    """Small reference to another Observatory v2 resource."""

    kind: str
    id: str
    label: str


class V2Action(BaseModel):
    """Provider-neutral action descriptor."""

    id: str
    label: str
    kind: str
    enabled: bool = False
    requires_confirmation: bool = True
    reason: str | None = None


class V2Service(BaseModel):
    """Provider-neutral service summary."""

    id: str
    name: str
    kind: str
    status: ServiceStatus
    health: V2Health
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
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    limit: int = 50
    offset: int = 0
    has_more: bool = False


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
