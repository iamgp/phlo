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


def clear_live_tables() -> None:
    """Clear live table declarations for tests and reloads."""
    _LIVE_TABLES.clear()
