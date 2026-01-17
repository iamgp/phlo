"""Observatory extension discovery utilities."""

from __future__ import annotations

import importlib.metadata

from phlo.config import get_settings
from phlo.logging import get_logger
from phlo_observatory import ObservatoryExtensionPlugin

logger = get_logger(__name__)

_ENTRY_POINT_GROUP = "phlo.plugins.observatory"


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
