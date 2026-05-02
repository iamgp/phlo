"""Provider-neutral Observatory v2 catalog surface loaders."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import V2Health, V2SurfaceItem

_HEALTH_STATES = {"ok", "warning", "error", "unknown"}


def load_catalog_items() -> list[V2SurfaceItem]:
    """Return catalog surface items."""
    try:
        raw_items = _load_backend_items()
    except Exception:
        return []

    if not isinstance(raw_items, list):
        return []

    return [
        _normalize_catalog_item(raw_item) for raw_item in raw_items if isinstance(raw_item, Mapping)
    ]


def _load_backend_items() -> list[Mapping[str, Any]]:
    """Load provider-native catalog items when stable hooks are available."""
    return []


def _normalize_catalog_item(raw: Mapping[str, Any]) -> V2SurfaceItem:
    item_id = _first_non_empty_string(raw, ("id", "name"), "catalog")
    name = _first_non_empty_string(raw, ("name", "id"), item_id)
    summary = _optional_non_empty_string(raw.get("summary"))
    metadata = _safe_item_metadata(raw.get("metadata"))

    return V2SurfaceItem(
        id=item_id,
        name=name,
        kind=_first_non_empty_string(raw, ("kind", "type"), "catalog"),
        health=_normalize_health(raw.get("health")),
        summary=summary,
        metadata=metadata,
    )


def _safe_item_metadata(value: Any) -> dict[str, Any]:
    metadata = safe_metadata(value)
    metadata.pop("native_links", None)
    return metadata


def _first_non_empty_string(raw: Mapping[str, Any], keys: tuple[str, ...], default: str) -> str:
    for key in keys:
        value = _optional_non_empty_string(raw.get(key))
        if value is not None:
            return value
    return default


def _optional_non_empty_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_health(value: Any) -> V2Health:
    if isinstance(value, str):
        return V2Health(state=value if value in _HEALTH_STATES else "unknown")

    if isinstance(value, Mapping):
        state = value.get("state")
        message = _optional_non_empty_string(value.get("message"))
        if isinstance(state, str) and state in _HEALTH_STATES:
            return V2Health(state=state, message=message)

    return V2Health(state="unknown")
