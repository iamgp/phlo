"""Project-root-aware caches for configuration entry points."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Protocol, TypeVar, cast

from phlo.config.env import resolve_project_root, use_project_root

T = TypeVar("T")


class ProjectRootCached(Protocol[T]):
    """Callable configuration cache with the standard invalidation hook."""

    def __call__(self, project_root: Path | str | None = None) -> T: ...

    def cache_clear(self) -> None: ...

    def cache_info(self) -> Any: ...


def project_root_cached(factory: Callable[[Path], T]) -> ProjectRootCached[T]:
    """Cache a configuration factory by its resolved project root.

    The returned callable accepts an optional ``project_root`` argument and
    keeps the usual ``cache_clear`` and ``cache_info`` methods used by tests
    and long-running processes to invalidate configuration deliberately.
    """
    cached = lru_cache(maxsize=16)(factory)

    @wraps(factory)
    def get_cached(project_root: Path | str | None = None) -> T:
        root = resolve_project_root(project_root)
        with use_project_root(root):
            return cached(root)

    result = cast(Any, get_cached)
    result.cache_clear = cached.cache_clear
    result.cache_info = cached.cache_info
    return cast(ProjectRootCached[T], result)
