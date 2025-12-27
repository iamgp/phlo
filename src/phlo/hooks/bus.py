"""Hook bus implementation for dispatching plugin events."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from phlo.discovery import discover_plugins, get_global_registry
from phlo.hooks.events import HookEvent
from phlo.plugins.hooks import (
    FailurePolicy,
    HookFilter,
    HookHandler,
    HookProvider,
    HookRegistration,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisteredHook:
    """Internal record for a registered hook handler."""

    plugin_name: str
    hook_name: str
    handler: Callable[[HookEvent], None] | HookHandler
    priority: int
    filters: HookFilter | None
    failure_policy: FailurePolicy


class HookBus:
    """Dispatch hook events to registered handlers."""

    def __init__(self) -> None:
        self._hooks: list[RegisteredHook] = []
        self._discovered = False

    def emit(self, event: HookEvent) -> None:
        """Emit an event to all matching hooks."""
        self._ensure_discovered()
        for hook in sorted(
            self._hooks, key=lambda item: (item.priority, item.plugin_name, item.hook_name)
        ):
            if hook.filters and not self._matches_filters(hook.filters, event):
                continue
            try:
                self._invoke_handler(hook.handler, event)
            except Exception as exc:
                policy = hook.failure_policy
                if policy == FailurePolicy.IGNORE:
                    continue
                if policy == FailurePolicy.LOG:
                    logger.exception(
                        "Hook failed: %s.%s (%s)",
                        hook.plugin_name,
                        hook.hook_name,
                        exc,
                    )
                    continue
                raise

    def register(self, registration: HookRegistration, *, plugin_name: str) -> None:
        """Register a hook handler."""
        self._hooks.append(
            RegisteredHook(
                plugin_name=plugin_name,
                hook_name=registration.hook_name,
                handler=registration.handler,
                priority=registration.priority,
                filters=registration.filters,
                failure_policy=registration.failure_policy,
            )
        )

    def register_provider(self, provider: HookProvider, *, plugin_name: str | None = None) -> None:
        """Register hooks from a provider."""
        resolved_name = plugin_name or _resolve_plugin_name(provider) or "unknown"
        for hook in provider.get_hooks():
            self.register(hook, plugin_name=resolved_name)

    def clear(self) -> None:
        """Remove all registered hooks."""
        self._hooks.clear()
        self._discovered = False

    def _ensure_discovered(self) -> None:
        """Discover plugins and register hook providers on first use."""

        if self._discovered:
            return
        discover_plugins(auto_register=True)
        registry = get_global_registry()
        for plugin in registry.iter_plugins():
            if isinstance(plugin, HookProvider):
                self.register_provider(plugin)
        self._discovered = True

    @staticmethod
    def _invoke_handler(
        handler: Callable[[HookEvent], None] | HookHandler, event: HookEvent
    ) -> None:
        """Dispatch a hook handler regardless of implementation style."""

        if isinstance(handler, HookHandler):
            handler.handle_event(event)
            return
        handler(event)

    @staticmethod
    def _matches_filters(filters: HookFilter, event: HookEvent) -> bool:
        """Return whether an event satisfies the provided hook filters."""

        if filters.event_types and event.event_type not in filters.event_types:
            return False
        if filters.asset_keys:
            event_asset_keys = _event_asset_keys(event)
            if not event_asset_keys or not filters.asset_keys.intersection(event_asset_keys):
                return False
        if filters.tags:
            for key, value in filters.tags.items():
                if event.tags.get(key) != value:
                    return False
        return True


def _event_asset_keys(event: HookEvent) -> set[str]:
    """Collect asset keys from hook event payloads."""

    keys: set[str] = set()
    asset_key = getattr(event, "asset_key", None)
    if isinstance(asset_key, str):
        keys.add(asset_key)
    asset_keys = getattr(event, "asset_keys", None)
    if isinstance(asset_keys, Iterable) and not isinstance(asset_keys, (str, bytes)):
        for item in asset_keys:
            if isinstance(item, str):
                keys.add(item)
    return keys


def _resolve_plugin_name(provider: Any) -> str | None:
    """Resolve a plugin name from a provider metadata attribute."""

    metadata = getattr(provider, "metadata", None)
    if metadata is None:
        return None
    return getattr(metadata, "name", None)


_GLOBAL_HOOK_BUS = HookBus()


def get_hook_bus() -> HookBus:
    """Return the global hook bus singleton."""

    return _GLOBAL_HOOK_BUS
