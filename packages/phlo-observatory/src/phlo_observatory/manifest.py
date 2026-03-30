"""Observatory extension manifest models (backward-compatible re-exports).

This module provides backward-compatible access to Observatory extension manifest
data models. These models define the structure and metadata for Observatory UI
extensions, including routes, navigation items, settings panels, and UI slots.

These exports are maintained for backward compatibility. New code should import
directly from phlo.plugins.observatory.

Exported Models:
    - ObservatoryExtensionManifest: Complete extension manifest definition
    - ObservatoryExtensionCompatibility: Version compatibility requirements
    - ObservatoryExtensionUI: UI contribution definitions
    - ObservatoryExtensionRoute: Route configuration for navigation
    - ObservatoryExtensionNavItem: Navigation menu item definition
    - ObservatoryExtensionSettings: Settings schema and defaults
    - ObservatoryExtensionSettingsPanel: Settings UI panel configuration
    - ObservatoryExtensionSlot: UI slot injection points

Example:
    >>> from phlo_observatory.manifest import ObservatoryExtensionManifest
    >>> manifest = ObservatoryExtensionManifest(name="my-extension", version="1.0.0")

See Also:
    phlo.plugins.observatory: Source of truth for extension API definitions.

"""

from phlo.plugins.observatory import (
    ObservatoryExtensionCompatibility,
    ObservatoryExtensionManifest,
    ObservatoryExtensionNavItem,
    ObservatoryExtensionRoute,
    ObservatoryExtensionSettings,
    ObservatoryExtensionSettingsPanel,
    ObservatoryExtensionSlot,
    ObservatoryExtensionUI,
)

__all__ = [
    "ObservatoryExtensionCompatibility",
    "ObservatoryExtensionManifest",
    "ObservatoryExtensionNavItem",
    "ObservatoryExtensionRoute",
    "ObservatoryExtensionSettings",
    "ObservatoryExtensionSettingsPanel",
    "ObservatoryExtensionSlot",
    "ObservatoryExtensionUI",
]
