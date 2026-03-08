"""Plugin entry-point discovery and loading."""

from __future__ import annotations

import importlib.metadata

from phlo.config import get_settings
from phlo.logging import get_logger, suppress_log_routing
from phlo.plugins.base import Plugin
from phlo.plugins.discovery._plugin_constants import ENTRY_POINT_GROUPS, PLUGIN_EXPECTED_TYPES
from phlo.plugins.discovery._plugin_lifecycle import register_plugin_with_lifecycle

logger = get_logger(__name__)


def is_plugin_allowed(plugin_name: str) -> bool:
    """Check if a plugin is allowed based on whitelist/blacklist configuration."""
    settings = get_settings()

    if plugin_name in settings.plugins_blacklist:
        logger.debug("plugin_blacklisted_skipping", plugin_name=plugin_name)
        return False

    if settings.plugins_whitelist and plugin_name not in settings.plugins_whitelist:
        logger.debug("plugin_not_whitelisted_skipping", plugin_name=plugin_name)
        return False

    return True


def discover_plugins(
    plugin_type: str | None = None,
    auto_register: bool = True,
    *,
    failure_level: str = "error",
) -> dict[str, list[Plugin]]:
    """Discover installed Phlo plugins from entry points."""
    settings = get_settings()

    with suppress_log_routing():
        if not settings.plugins_enabled:
            logger.info("Plugin system is disabled")
            return {key: [] for key in ENTRY_POINT_GROUPS}

        discovered: dict[str, list[Plugin]] = {key: [] for key in ENTRY_POINT_GROUPS}
        types_to_discover = [plugin_type] if plugin_type else list(ENTRY_POINT_GROUPS)

        for current_type in types_to_discover:
            if current_type not in ENTRY_POINT_GROUPS:
                logger.warning("unknown_plugin_type", plugin_type=current_type)
                continue

            entry_point_group = ENTRY_POINT_GROUPS[current_type]

            logger.info(
                "plugin_discovery_started",
                plugin_type=current_type,
                entry_point_group=entry_point_group,
            )

            try:
                entry_points = importlib.metadata.entry_points(group=entry_point_group)
            except TypeError:
                all_entry_points = importlib.metadata.entry_points()
                entry_points = all_entry_points.get(entry_point_group, [])

            for entry_point in entry_points:
                try:
                    if not is_plugin_allowed(entry_point.name):
                        continue

                    logger.info(
                        "plugin_loading",
                        plugin_name=entry_point.name,
                        entry_point=entry_point.value,
                    )

                    plugin_candidate = entry_point.load()
                    plugin = (
                        plugin_candidate()
                        if isinstance(plugin_candidate, type)
                        else plugin_candidate
                    )

                    if not isinstance(plugin, Plugin):
                        logger.error(
                            "plugin_invalid_base_class",
                            plugin_name=entry_point.name,
                        )
                        continue

                    expected_type = PLUGIN_EXPECTED_TYPES[current_type]
                    if not isinstance(plugin, expected_type):
                        logger.error(
                            "plugin_incorrect_type",
                            plugin_name=entry_point.name,
                            expected_type=expected_type.__name__,
                            actual_type=type(plugin).__name__,
                        )
                        continue

                    if auto_register:
                        register_plugin_with_lifecycle(current_type, plugin, replace=True)

                    discovered[current_type].append(plugin)

                    logger.debug(
                        "plugin_loaded",
                        plugin_name=plugin.metadata.name,
                        plugin_version=plugin.metadata.version,
                        plugin_type=current_type,
                    )
                except Exception:
                    log_method = getattr(logger, failure_level, logger.error)
                    log_method(
                        "plugin_load_failed",
                        plugin_name=entry_point.name,
                        entry_point=entry_point.value,
                        plugin_type=current_type,
                        exc_info=True,
                    )
                    continue

        total = sum(len(plugins) for plugins in discovered.values())
        logger.debug("plugin_discovery_completed", total_plugins=total, discovered=discovered)

        return discovered
