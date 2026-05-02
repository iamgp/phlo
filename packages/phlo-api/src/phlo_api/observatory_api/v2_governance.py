"""Provider-neutral Observatory v2 governance surface loaders."""

from __future__ import annotations

from phlo_api.observatory_api.v2_models import V2SurfaceItem


def load_governance_items() -> list[V2SurfaceItem]:
    """Return governance surface items."""
    return []
