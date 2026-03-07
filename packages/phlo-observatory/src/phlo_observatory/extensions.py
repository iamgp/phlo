"""Backward-compatible re-exports for Observatory extension discovery."""

from phlo.plugins.observatory import (
    ObservatoryExtensionPlugin,
    discover_observatory_extensions,
    get_observatory_extension,
)

__all__ = [
    "ObservatoryExtensionPlugin",
    "discover_observatory_extensions",
    "get_observatory_extension",
]
