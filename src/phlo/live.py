"""Managed live table declarations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

_SUPPORTED_MODES = {"incremental", "full"}
_LIVE_TABLES: list[LiveTableSpec] = []


@dataclass(frozen=True, slots=True)
class LiveTableSpec:
    name: str
    query: str
    sources: tuple[str, ...]
    target_lag: str | None
    mode: str
    quality: tuple[str, ...]
    metadata: dict[str, Any]
    fn: Callable[..., Any]


def live_table(
    *,
    name: str,
    query: str,
    sources: list[str] | tuple[str, ...] | None = None,
    target_lag: str | None = None,
    mode: str = "incremental",
    quality: list[str] | tuple[str, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Declare a managed table that Phlo can refresh from upstream sources."""
    if mode not in _SUPPORTED_MODES:
        raise ValueError(f"Unsupported live table mode: {mode}")

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        _LIVE_TABLES.append(
            LiveTableSpec(
                name=name,
                query=query,
                sources=tuple(sources or ()),
                target_lag=target_lag,
                mode=mode,
                quality=tuple(quality or ()),
                metadata=dict(metadata or {}),
                fn=fn,
            )
        )
        return fn

    return _decorator


def get_live_tables() -> list[LiveTableSpec]:
    """Return registered live table declarations."""
    return list(_LIVE_TABLES)


def plan_live_tables() -> list[dict[str, Any]]:
    """Return live tables in dependency order and validate source references."""
    by_name = {spec.name: spec for spec in _LIVE_TABLES}
    planned: list[LiveTableSpec] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(spec: LiveTableSpec) -> None:
        if spec.name in visited:
            return
        if spec.name in visiting:
            raise ValueError(f"Live table dependency cycle includes {spec.name}")
        visiting.add(spec.name)
        for source in spec.sources:
            if source in by_name:
                visit(by_name[source])
            elif "." in source:
                raise ValueError(f"{spec.name} depends on unknown live table source {source}")
        visiting.remove(spec.name)
        visited.add(spec.name)
        planned.append(spec)

    for spec in _LIVE_TABLES:
        visit(spec)

    return [
        {
            "name": spec.name,
            "query": spec.query,
            "sources": list(spec.sources),
            "target_lag": spec.target_lag,
            "mode": spec.mode,
            "quality": list(spec.quality),
            "metadata": dict(spec.metadata),
        }
        for spec in planned
    ]


def clear_live_tables() -> None:
    """Clear live table declarations for tests and reloads."""
    _LIVE_TABLES.clear()
