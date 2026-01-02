"""Registry client for Phlo plugins."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import requests

from phlo.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistryPlugin:
    """Normalized plugin entry from the registry."""

    name: str
    type: str
    package: str
    version: str
    description: str
    author: str
    homepage: str | None
    tags: list[str]
    verified: bool
    core: bool


_REGISTRY_CACHE: dict[str, Any] = {
    "loaded_at": 0.0,
    "data": None,
}


def _is_cache_valid(now: float, ttl_seconds: int) -> bool:
    if not _REGISTRY_CACHE["data"]:
        return False
    return (now - _REGISTRY_CACHE["loaded_at"]) < ttl_seconds


def _normalize_registry(registry: dict[str, Any]) -> list[RegistryPlugin]:
    plugins = []
    for name, info in registry.get("plugins", {}).items():
        plugins.append(
            RegistryPlugin(
                name=name,
                type=info.get("type", ""),
                package=info.get("package", ""),
                version=info.get("version", ""),
                description=info.get("description", ""),
                author=info.get("author", ""),
                homepage=info.get("homepage"),
                tags=list(info.get("tags", [])),
                verified=bool(info.get("verified", False)),
                core=bool(info.get("core", False)),
            )
        )
    return plugins


def _load_registry_from_package() -> dict[str, Any]:
    registry_path = resources.files("phlo.plugins").joinpath("registry_data.json")
    return json.loads(registry_path.read_text(encoding="utf-8"))


def _load_registry_from_repo() -> dict[str, Any] | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "registry" / "plugins.json"
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def _load_registry_from_local() -> dict[str, Any]:
    try:
        return _load_registry_from_package()
    except Exception as exc:
        logger.debug("Failed to load registry from package: %s", exc)

    repo_registry = _load_registry_from_repo()
    if repo_registry:
        return repo_registry

    raise FileNotFoundError("No bundled registry data found.")


def _validate_registry(registry: dict[str, Any]) -> None:
    if not isinstance(registry, dict) or "plugins" not in registry:
        raise ValueError("Registry payload missing plugins section.")


def clear_registry_cache() -> None:
    """Clear registry cache (useful for tests)."""
    _REGISTRY_CACHE["loaded_at"] = 0.0
    _REGISTRY_CACHE["data"] = None


def fetch_registry(force_refresh: bool = False) -> dict[str, Any]:
    """
    Fetch the plugin registry with caching.

    Falls back to bundled registry data if network fetch fails.
    """
    settings = get_settings()
    ttl_seconds = settings.plugin_registry_cache_ttl_seconds
    now = time.time()

    if not force_refresh and _is_cache_valid(now, ttl_seconds):
        return _REGISTRY_CACHE["data"]

    registry = None
    registry_url = settings.plugin_registry_url
    if registry_url:
        try:
            response = requests.get(registry_url, timeout=settings.plugin_registry_timeout_seconds)
            response.raise_for_status()
            registry = response.json()
            _validate_registry(registry)
        except Exception as exc:
            logger.warning("Registry fetch failed, using bundled data: %s", exc)

    if registry is None:
        registry = _load_registry_from_local()
        _validate_registry(registry)

    _REGISTRY_CACHE["loaded_at"] = now
    _REGISTRY_CACHE["data"] = registry
    return registry


def list_registry_plugins() -> list[RegistryPlugin]:
    """Return all registry plugins as normalized entries."""
    registry = fetch_registry()
    return _normalize_registry(registry)


def get_registry_data() -> dict[str, Any]:
    """Return raw registry data payload."""
    return fetch_registry()


def get_plugin(name: str) -> RegistryPlugin | None:
    """Return a single plugin entry by name."""
    registry = fetch_registry()
    info = registry.get("plugins", {}).get(name)
    if not info:
        return None
    return _normalize_registry({"plugins": {name: info}})[0]


def search_plugins(
    query: str | None = None,
    plugin_type: str | None = None,
    tags: list[str] | None = None,
) -> list[RegistryPlugin]:
    """Search registry plugins by name, description, type, or tags."""
    plugins = list_registry_plugins()

    if plugin_type:
        plugins = [plugin for plugin in plugins if plugin.type == plugin_type]

    if tags:
        tag_set = {tag.lower() for tag in tags}
        plugins = [
            plugin for plugin in plugins if tag_set.issubset({tag.lower() for tag in plugin.tags})
        ]

    if query:
        query_lower = query.lower()

        def matches(plugin: RegistryPlugin) -> bool:
            if query_lower in plugin.name.lower():
                return True
            if query_lower in plugin.description.lower():
                return True
            if query_lower in plugin.package.lower():
                return True
            return any(query_lower in tag.lower() for tag in plugin.tags)

        plugins = [plugin for plugin in plugins if matches(plugin)]

    return plugins
