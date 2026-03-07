"""Capability resolution helpers for phlo-openmetadata."""

from __future__ import annotations

from phlo.capabilities import resolve_capability
from phlo.capabilities.interfaces import CatalogScanner
from phlo.capabilities.discovery import discover_capabilities


def resolve_catalog_scanner(name: str | None = None) -> CatalogScanner:
    """Resolve a catalog scanner capability for metadata sync flows."""
    discover_capabilities()
    resolution = resolve_capability("catalog_scanner", name)
    if resolution is None:
        if name:
            raise RuntimeError(f"Catalog scanner capability '{name}' is not available.")
        raise RuntimeError("No catalog scanner capability is available.")
    return resolution.provider
