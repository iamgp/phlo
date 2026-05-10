"""Search result composition for Observatory v2."""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote

from phlo_api.observatory_api.v2_models import (
    V2Asset,
    V2Extension,
    V2Operation,
    V2QualityCheck,
    V2SearchResult,
    V2Service,
    V2Table,
)


def search_results(
    *,
    query: str,
    services: Sequence[V2Service],
    assets: Sequence[V2Asset],
    tables: Sequence[V2Table],
    operations: Sequence[V2Operation],
    quality: Sequence[V2QualityCheck] = (),
    extensions: Sequence[V2Extension] = (),
) -> list[V2SearchResult]:
    needle = query.strip().lower()
    if not needle:
        return []

    results: list[V2SearchResult] = []
    for service in services:
        haystack = " ".join([service.id, service.name, service.kind, service.status]).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"service:{service.id}",
                    label=service.name,
                    kind="service",
                    summary=f"{service.kind} · {service.status}",
                    href="/services",
                )
            )

    for asset in assets:
        haystack = " ".join(
            [asset.id, asset.name, asset.group or "", asset.description or "", *asset.kinds]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"asset:{asset.id}",
                    label=asset.name,
                    kind="asset",
                    summary=asset.description or asset.group,
                    href=f"/asset/{route_path_segment(asset.id)}",
                )
            )

    for table in tables:
        haystack = " ".join(
            [table.id, table.name, table.namespace or "", table.format or "", table.branch or ""]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"table:{table.id}",
                    label=table.namespace + "." + table.name if table.namespace else table.name,
                    kind="table",
                    summary=f"{table.format or 'table'} · {table.branch or 'main'}",
                    href=f"/table/{route_path_segment(table.id)}",
                )
            )

    for operation in operations:
        haystack = " ".join([operation.id, operation.name, operation.kind, operation.status]).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"operation:{operation.id}",
                    label=operation.name,
                    kind="operation",
                    summary=f"{operation.kind} · {operation.status}",
                    href=f"/operations/{route_path_segment(operation.id)}",
                )
            )

    for check in quality:
        haystack = " ".join(
            [check.id, check.name, check.asset_id, check.status, check.severity or ""]
        ).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"quality:{check.id}",
                    label=check.name,
                    kind="quality",
                    summary=f"{check.asset_id} · {check.status}",
                    href="/quality",
                )
            )

    for extension in extensions:
        haystack = " ".join([extension.id, extension.name, extension.version or ""]).lower()
        if needle in haystack:
            results.append(
                V2SearchResult(
                    id=f"extension:{extension.id}",
                    label=extension.name,
                    kind="extension",
                    summary=extension.settings_scope or extension.version,
                    href=f"/extension/{route_path_segment(extension.id)}",
                )
            )

    return results[:25]


def route_path_segment(resource_id: str) -> str:
    return quote(resource_id, safe="")
