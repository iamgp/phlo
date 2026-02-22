"""Plugin discovery public compatibility layer."""

from __future__ import annotations

from phlo.logging import get_logger
from phlo.plugins.discovery._plugin_auto_discovery import (
    auto_discover as _auto_discover,
)
from phlo.plugins.discovery._plugin_auto_discovery import (
    is_auto_discover_disabled_by_env as _is_auto_discover_disabled_by_env_impl,
)
from phlo.plugins.discovery._plugin_auto_discovery import (
    should_auto_discover as _should_auto_discover_impl,
)
from phlo.plugins.discovery._plugin_constants import (
    ENTRY_POINT_GROUPS as _ENTRY_POINT_GROUPS,
)
from phlo.plugins.discovery._plugin_constants import (
    FALSY_ENV_VALUES,
    NO_AUTO_DISCOVER_ENV,
    PLUGIN_EXPECTED_TYPES,
    PLUGIN_GETTER_METHODS,
    PLUGIN_REGISTER_METHODS,
    TRUTHY_ENV_VALUES,
)
from phlo.plugins.discovery._plugin_lifecycle import (
    register_plugin_with_lifecycle as _register_plugin_with_lifecycle_impl,
)
from phlo.plugins.discovery._plugin_loading import (
    discover_plugins as _discover_plugins,
)
from phlo.plugins.discovery._plugin_loading import (
    is_plugin_allowed as _is_plugin_allowed_impl,
)
from phlo.plugins.discovery._plugin_queries import (
    get_hook_plugin as _get_hook_plugin,
)
from phlo.plugins.discovery._plugin_queries import (
    get_plugin as _get_plugin,
)
from phlo.plugins.discovery._plugin_queries import (
    get_plugin_info as _get_plugin_info,
)
from phlo.plugins.discovery._plugin_queries import (
    get_quality_check as _get_quality_check,
)
from phlo.plugins.discovery._plugin_queries import (
    get_service as _get_service,
)
from phlo.plugins.discovery._plugin_queries import (
    get_source_connector as _get_source_connector,
)
from phlo.plugins.discovery._plugin_queries import (
    get_transformation as _get_transformation,
)
from phlo.plugins.discovery._plugin_queries import (
    list_plugins as _list_plugins,
)
from phlo.plugins.discovery._plugin_queries import (
    validate_plugins as _validate_plugins,
)

logger = get_logger(__name__)

# Backward-compatible private constant names.
_NO_AUTO_DISCOVER_ENV = NO_AUTO_DISCOVER_ENV
_TRUTHY_ENV_VALUES = TRUTHY_ENV_VALUES
_FALSY_ENV_VALUES = FALSY_ENV_VALUES
_PLUGIN_REGISTER_METHODS = PLUGIN_REGISTER_METHODS
_PLUGIN_GETTER_METHODS = PLUGIN_GETTER_METHODS
_PLUGIN_EXPECTED_TYPES = PLUGIN_EXPECTED_TYPES
ENTRY_POINT_GROUPS = _ENTRY_POINT_GROUPS
_is_plugin_allowed = _is_plugin_allowed_impl
_register_plugin_with_lifecycle = _register_plugin_with_lifecycle_impl
_is_auto_discover_disabled_by_env = _is_auto_discover_disabled_by_env_impl
_should_auto_discover = _should_auto_discover_impl

discover_plugins = _discover_plugins
list_plugins = _list_plugins
get_plugin = _get_plugin
get_source_connector = _get_source_connector
get_quality_check = _get_quality_check
get_transformation = _get_transformation
get_service = _get_service
get_hook_plugin = _get_hook_plugin
get_plugin_info = _get_plugin_info
validate_plugins = _validate_plugins
auto_discover = _auto_discover

# Auto-discover plugins when module is imported.
# `plugins_auto_discover` is the default; `PHLO_NO_AUTO_DISCOVER` has override precedence.
if _should_auto_discover():
    try:
        auto_discover()
    except Exception as exc:
        logger.warning(
            "plugin_auto_discovery_failed",
            error=str(exc),
            hint=(
                "Set PHLO_NO_AUTO_DISCOVER=1 to skip auto-discovery "
                "or set plugins_auto_discover=false"
            ),
        )
