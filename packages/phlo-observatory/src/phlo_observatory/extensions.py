"""Observatory extension discovery utilities (backward-compatible re-exports).

This module provides backward-compatible access to extension discovery and
retrieval functions for the Observatory UI plugin system.

Extension Discovery:
    The Observatory uses Python entry points to discover UI extensions.
    Extensions declare themselves in package metadata and are loaded
    dynamically at runtime.

Key Functions:
    - discover_observatory_extensions: Scan and load all available extensions
    - get_observatory_extension: Retrieve a specific extension by name

Backward Compatibility:
    These exports are maintained for existing extensions. New code should
    import directly from phlo.plugins.observatory.

Example:
    >>> from phlo_observatory.extensions import discover_observatory_extensions
    >>> extensions = discover_observatory_extensions()
    >>> for ext in extensions:
    ...     print(f"Found extension: {ext.manifest.name}")

See Also:
    phlo.plugins.observatory: Source of truth for extension API.
    phlo_observatory.manifest: Extension manifest data models.

"""

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
