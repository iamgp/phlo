"""Provider-neutral Observatory v2 product surface loaders."""

from __future__ import annotations

from phlo_api.observatory_api.v2_models import V2SurfaceItem


def load_api_items() -> list[V2SurfaceItem]:
    """Return API surface items."""
    return []


def load_bi_items() -> list[V2SurfaceItem]:
    """Return BI surface items."""
    return []
