"""Provider-neutral Observatory v2 observability surface loaders."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import HealthState, V2Health, V2SurfaceItem

_HEALTH_STATES: set[HealthState] = {"ok", "warning", "error", "unknown"}


def load_observability_items() -> list[V2SurfaceItem]:
    """Return observability surface items."""
    try:
        raw_items = _load_backend_links()
    except Exception:
        return []

    if not isinstance(raw_items, list):
        return []

    return [
        _normalize_observability_item(raw_item, index)
        for index, raw_item in enumerate(raw_items)
        if isinstance(raw_item, Mapping)
    ]


def _load_backend_links() -> list[Mapping[str, Any]]:
    """Return raw observability backend summaries."""
    return []


def _normalize_observability_item(raw_item: Mapping[str, Any], index: int) -> V2SurfaceItem:
    item_id = _safe_string(raw_item.get("id")) or _safe_string(raw_item.get("name"))
    if item_id is None:
        item_id = f"observability-item-{index + 1}"

    name = _safe_string(raw_item.get("name")) or item_id
    kind = _safe_string(raw_item.get("kind")) or "observability"
    summary = _safe_string(raw_item.get("summary"))
    metadata = _safe_item_metadata(raw_item.get("metadata"))

    return V2SurfaceItem(
        id=item_id,
        name=name,
        kind=kind,
        health=_normalize_health(raw_item.get("health")),
        summary=summary,
        metadata=metadata,
    )


def _normalize_health(value: Any) -> V2Health:
    if isinstance(value, str):
        state = _safe_health_state(value.strip())
        if state in _HEALTH_STATES:
            return V2Health(state=state)

    if isinstance(value, Mapping):
        state = _safe_health_state(_safe_string(value.get("state")))
        if state in _HEALTH_STATES:
            return V2Health(state=state, message=_safe_string(value.get("message")))

    return V2Health(state="unknown")


def _safe_item_metadata(value: Any) -> dict[str, Any]:
    metadata = safe_metadata(value)
    metadata.pop("native_links", None)
    return metadata


def _safe_health_state(value: str | None) -> HealthState | None:
    if value in _HEALTH_STATES:
        return cast(HealthState, value)
    return None


def _safe_string(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None
    return text
