"""Core contracts and discovery helpers for Observatory extensions."""

from __future__ import annotations

import importlib.metadata
from abc import ABC, abstractmethod
from importlib.resources.abc import Traversable
from typing import Any, Literal

from pydantic import BaseModel, Field

from phlo.config import get_settings
from phlo.logging import get_logger
from phlo.plugins.base.plugin import Plugin

logger = get_logger(__name__)

_ENTRY_POINT_GROUP = "phlo.plugins.observatory"


class ObservatoryExtensionCompatibility(BaseModel):
    """Compatibility requirements for an Observatory extension."""

    observatory_min: str = Field(..., description="Minimum supported Observatory version")


class ObservatoryExtensionSettings(BaseModel):
    """Settings schema and defaults for an extension."""

    settings_schema: dict[str, Any] = Field(
        ..., description="Schema for extension settings and validation"
    )
    defaults: dict[str, Any] = Field(default_factory=dict)
    scope: Literal["global", "extension"] = "extension"


class ObservatoryExtensionRoute(BaseModel):
    """Route registration entry for an extension."""

    path: str
    module: str
    export: str = "registerRoutes"


class ObservatoryExtensionNavItem(BaseModel):
    """Navigation entry for an extension."""

    title: str
    to: str


class ObservatoryExtensionSlot(BaseModel):
    """Slot registration entry for an extension."""

    slot_id: str
    module: str
    export: str = "registerSlot"


class ObservatoryExtensionSettingsPanel(BaseModel):
    """Settings panel registration entry for an extension."""

    module: str
    export: str = "registerSettings"


class ObservatoryExtensionUI(BaseModel):
    """UI contributions for an extension."""

    routes: list[ObservatoryExtensionRoute] = Field(default_factory=list)
    nav: list[ObservatoryExtensionNavItem] = Field(default_factory=list)
    slots: list[ObservatoryExtensionSlot] = Field(default_factory=list)
    settings: list[ObservatoryExtensionSettingsPanel] = Field(default_factory=list)


class ObservatoryExtensionManifest(BaseModel):
    """Manifest contract for Observatory extensions."""

    name: str
    version: str
    compat: ObservatoryExtensionCompatibility
    settings: ObservatoryExtensionSettings | None = None
    ui: ObservatoryExtensionUI = Field(default_factory=ObservatoryExtensionUI)


class ObservatoryExtensionPlugin(Plugin, ABC):
    """Base class for Observatory UI extension plugins."""

    @property
    @abstractmethod
    def manifest(self) -> ObservatoryExtensionManifest | dict[str, Any]:
        """Return the extension manifest or a raw manifest dict."""
        ...

    @property
    @abstractmethod
    def asset_root(self) -> Traversable:
        """Return the root directory that contains the extension assets."""
        ...

    def get_manifest(self) -> ObservatoryExtensionManifest:
        """Return a validated manifest instance."""
        if isinstance(self.manifest, ObservatoryExtensionManifest):
            return self.manifest
        return ObservatoryExtensionManifest.model_validate(self.manifest)


def _is_plugin_allowed(plugin_name: str) -> bool:
    settings = get_settings()
    if plugin_name in settings.plugins_blacklist:
        logger.debug("Plugin '%s' is blacklisted, skipping", plugin_name)
        return False
    if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
        logger.debug("Plugin '%s' is not in whitelist, skipping", plugin_name)
        return False
    return True


def discover_observatory_extensions() -> list[ObservatoryExtensionPlugin]:
    """Discover installed Observatory extension plugins."""
    settings = get_settings()
    if not settings.plugins_enabled:
        logger.info("Plugin system is disabled")
        return []

    try:
        entry_points = importlib.metadata.entry_points(group=_ENTRY_POINT_GROUP)
    except TypeError:
        entry_points = importlib.metadata.entry_points().get(_ENTRY_POINT_GROUP, [])

    plugins: list[ObservatoryExtensionPlugin] = []
    for entry_point in entry_points:
        if not _is_plugin_allowed(entry_point.name):
            continue
        try:
            plugin_class = entry_point.load()
            plugin = plugin_class() if isinstance(plugin_class, type) else plugin_class
        except Exception as exc:
            logger.warning("Failed to load Observatory extension %s: %s", entry_point.name, exc)
            continue
        if not isinstance(plugin, ObservatoryExtensionPlugin):
            logger.warning(
                "Observatory extension %s has invalid type %s",
                entry_point.name,
                type(plugin).__name__,
            )
            continue
        plugins.append(plugin)

    return plugins


def get_observatory_extension(name: str) -> ObservatoryExtensionPlugin | None:
    """Return a single Observatory extension by name."""
    for plugin in discover_observatory_extensions():
        if plugin.metadata.name == name:
            return plugin
    return None
