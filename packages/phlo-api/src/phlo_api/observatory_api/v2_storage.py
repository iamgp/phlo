"""Provider-neutral Observatory v2 storage surface loaders."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from phlo_api.observatory_api.v2_metadata import safe_metadata
from phlo_api.observatory_api.v2_models import V2Health, V2SurfaceItem

_VALID_HEALTH_STATES = {"ok", "warning", "error", "unknown"}


def load_storage_items() -> list[V2SurfaceItem]:
    """Return storage surface items."""
    try:
        raw_items = _load_backend_items()
    except Exception:
        return []

    if not isinstance(raw_items, list):
        return []

    return [
        _normalize_storage_item(raw, index=index)
        for index, raw in enumerate(raw_items, start=1)
        if isinstance(raw, Mapping)
    ]


def _load_backend_items() -> list[Mapping[str, Any]]:
    """Load raw storage surface mappings from installed providers."""
    return []


def _normalize_storage_item(raw: Mapping[str, Any], *, index: int) -> V2SurfaceItem:
    fallback_id = f"storage-{index}"
    item_id = _string_or_default(raw.get("id"), fallback_id)
    name = _string_or_default(raw.get("name"), item_id)
    kind = _string_or_default(raw.get("kind"), "storage")
    summary = _optional_non_empty_string(raw.get("summary"))

    return V2SurfaceItem(
        id=item_id,
        name=name,
        kind=kind,
        health=_normalize_health(raw.get("health")),
        summary=summary,
        metadata=_safe_item_metadata(raw.get("metadata")),
    )


def _safe_item_metadata(value: Any) -> dict[str, Any]:
    metadata = safe_metadata(value)
    metadata.pop("native_links", None)
    return metadata


def _normalize_health(value: Any) -> V2Health:
    if isinstance(value, str) and value in _VALID_HEALTH_STATES:
        return V2Health(state=value)

    if isinstance(value, Mapping):
        state = value.get("state")
        message = _optional_non_empty_string(value.get("message"))
        if isinstance(state, str) and state in _VALID_HEALTH_STATES:
            return V2Health(state=state, message=message)

    return V2Health(state="unknown")


def _string_or_default(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _optional_non_empty_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
